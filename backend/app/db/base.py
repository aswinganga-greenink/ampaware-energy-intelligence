"""
app/db/base.py
==============
SQLAlchemy declarative base and shared column mixins.

All ORM models must inherit from Base.
Mixins provide standardised columns (id, timestamps, soft-delete)
that every table in the schema uses — ensuring consistency and
making schema migrations predictable.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Root declarative base.

    All ORM models import from this module:
        from app.db.base import Base
    """

    # Allow arbitrary Python types in type annotations of mapped columns
    type_annotation_map: dict = {}  # type: ignore[type-arg]


# ---------------------------------------------------------------------------
# Column mixins
# ---------------------------------------------------------------------------


class UUIDPrimaryKeyMixin:
    """
    UUID primary key column.

    Uses PostgreSQL's native UUID type.
    server_default generates the UUID on the DB side — this avoids the
    overhead of an extra round-trip and keeps IDs truly random even if
    the Python layer is bypassed (e.g., direct DB inserts during migrations).
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
        index=True,
        comment="Primary key — UUID v4",
    )


class TimestampMixin:
    """
    Automatic created_at / updated_at columns.

    - created_at is set once at INSERT time via server_default.
    - updated_at is refreshed on every UPDATE via onupdate.
    Both are stored in UTC (timezone=True).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Row creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Row last-update timestamp (UTC)",
    )


class SoftDeleteMixin:
    """
    Soft-delete support.

    Rather than physically deleting rows (which destroys audit trails),
    we set is_deleted=True and deleted_at=<timestamp>.

    All repository queries MUST filter on is_deleted=False by default.
    Only explicit "include_deleted" queries should skip this filter.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
        comment="Soft-delete flag",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of soft deletion (UTC)",
    )


class AuditableMixin(UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Most tables need UUID PK + timestamps.
    Combine for convenience.
    """


class FullAuditMixin(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """
    Full audit mixin for entities that need soft-delete.
    Use for Users, Devices, Tariffs, etc.
    """
