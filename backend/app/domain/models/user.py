"""
app/domain/models/user.py
==========================
User account and RBAC ORM models.

Tables:
  users                 — platform user accounts
  user_api_keys         — device/service API keys (separate from JWTs)

Design decisions:
- Passwords are stored as bcrypt hashes (never plaintext).
- Roles are a single enum column — the platform has three well-defined roles
  and the complexity of a full permission table is not warranted at this scale.
  A permission table CAN be added in Phase 12 if fine-grained RBAC is needed.
- Email is the primary login identifier and is indexed (UNIQUE).
- phone is optional but stored for billing notifications.
- API keys use a separate table so they can be rotated/revoked independently.
- Soft delete: deactivating a user does NOT destroy their device/billing history.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, FullAuditMixin
from app.domain.enums.user_role import UserRole


class User(FullAuditMixin, Base):
    """
    Platform user account.

    Invariants:
    - email is unique and case-normalised to lowercase on write.
    - hashed_password uses bcrypt with cost factor ≥ 12.
    - A deactivated user (is_active=False) cannot authenticate.
    - A soft-deleted user is fully excluded from all queries.
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_role", "role"),
        Index("ix_users_is_active_deleted", "is_active", "is_deleted"),
        {"comment": "Platform user accounts with RBAC roles"},
    )

    # --- Identity ---
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Primary login identifier — stored lowercase",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name",
    )
    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        comment="E.164 format phone number for SMS notifications",
    )

    # --- Auth ---
    hashed_password: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="bcrypt hash — NEVER store plaintext",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="False = account suspended, cannot login",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="True once email is confirmed",
    )

    # --- RBAC ---
    role: Mapped[UserRole] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.CONSUMER,
        server_default=UserRole.CONSUMER.value,
        comment="ADMIN | OPERATOR | CONSUMER",
    )

    # --- Session security ---
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of last successful login",
    )
    failed_login_count: Mapped[int] = mapped_column(
        default=0,
        server_default="0",
        nullable=False,
        comment="Consecutive failed login attempts (reset on success)",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account locked until this UTC time after too many failed logins",
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of last password change (for token invalidation)",
    )

    # --- Relationships ---
    devices: Mapped[list["Device"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Device",
        back_populates="owner",
        foreign_keys="Device.owner_id",
        lazy="select",
    )
    api_keys: Mapped[list["UserApiKey"]] = relationship(
        "UserApiKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


class UserApiKey(Base):
    """
    Long-lived API keys for service-to-service authentication.

    Not used by device firmware (devices use device-specific keys).
    Used by external systems, monitoring dashboards, CI pipelines, etc.
    """

    __tablename__ = "user_api_keys"
    __table_args__ = (
        Index("ix_user_api_keys_key_hash", "key_hash", unique=True),
        Index("ix_user_api_keys_user_id", "user_id"),
        {"comment": "Revokable long-lived API keys for service accounts"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable label for this key (e.g., 'Grafana Dashboard')",
    )
    key_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="SHA-256 hash of the raw key — never store plaintext",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        comment="First 8 chars of raw key for identification without exposing it",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL = never expires",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationship ---
    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<UserApiKey id={self.id} prefix={self.key_prefix!r} user={self.user_id}>"
