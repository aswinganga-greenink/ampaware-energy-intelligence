"""
app/domain/models/audit.py
============================
Audit log, system events, and notification models.

Tables:
  audit_logs      — immutable record of every data mutation
  system_events   — structured business events (device online, tariff updated, etc.)
  notifications   — user-facing alerts generated from anomalies/events

Design decisions:
- audit_logs is append-only. No update, no delete, ever.
- old_values / new_values store the full row state as JSONB snapshots.
  This allows full reconstruction of any record at any point in time.
- ip_address uses PostgreSQL INET type for proper IP validation + indexing.
- system_events are machine-readable structured events consumed by:
  a) notification generators
  b) external webhooks (Phase 13+)
  c) event sourcing/replay (disaster recovery)
- notifications model the delivery lifecycle of user alerts.
  They are generated from system_events and anomaly_records.
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
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums.tariff import AuditAction, NotificationStatus, SystemEventType


class AuditLog(Base):
    """
    Immutable audit trail for all data mutations.

    Written by the service layer before/after every significant mutation.
    Used for:
    - Regulatory compliance (utility billing audit requirements)
    - Forensic investigation of data issues
    - Rollback capability (via old_values)

    Stored outside the main transaction where possible to survive rollbacks.
    (In practice, written in the same transaction but never rolled back manually.)
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_table_record", "table_name", "record_id"),
        Index("ix_audit_logs_changed_at", "changed_at"),
        Index("ix_audit_logs_changed_by", "changed_by_id"),
        Index("ix_audit_logs_action", "action"),
        {"comment": "Immutable audit trail for all data mutations"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    table_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the affected table",
    )
    record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Primary key of the affected row (NULL for bulk operations)",
    )
    action: Mapped[AuditAction] = mapped_column(
        String(20),
        nullable=False,
        comment="INSERT | UPDATE | DELETE | SOFT_DELETE | RESTORE",
    )
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who performed the action (NULL for system/automated actions)",
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="UTC timestamp of the change",
    )

    # --- State snapshots ---
    old_values: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Row state BEFORE the change (NULL for INSERT)",
    )
    new_values: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Row state AFTER the change (NULL for DELETE)",
    )

    # --- Request context ---
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        comment="Client IP address (PostgreSQL INET type)",
    )
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="X-Request-ID from the HTTP request (for correlating log lines)",
    )

    # Audit log has no updated_at — it is write-once
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog table={self.table_name!r} record={self.record_id} "
            f"action={self.action} at={self.changed_at}>"
        )


class SystemEvent(Base):
    """
    Structured business event record.

    System events represent significant state transitions in the platform.
    They are the backbone for:
    - Notification generation
    - External integrations (webhooks)
    - Event-driven audit trail
    - Operational dashboards

    payload is JSONB — each event_type has a defined schema (documented
    in the Phase 11 event catalog). The schema is validated at write time
    by the event publisher, not enforced at DB level for flexibility.
    """

    __tablename__ = "system_events"
    __table_args__ = (
        Index("ix_system_events_type", "event_type"),
        Index("ix_system_events_device_id", "device_id"),
        Index("ix_system_events_created_at", "created_at"),
        Index("ix_system_events_type_created", "event_type", "created_at"),
        {"comment": "Structured business events (device state, tariff changes, etc.)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_type: Mapped[SystemEventType] = mapped_column(
        String(100),
        nullable=False,
        comment="Structured event type from SystemEventType enum",
    )

    # --- Optional contextual references ---
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    anomaly_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("anomaly_records.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Payload ---
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'{}'",
        comment="Event-type-specific structured data",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SystemEvent type={self.event_type} at={self.created_at}>"


class Notification(Base):
    """
    User-facing alert delivered via in-app, push, or SMS channels.

    Notifications are generated from SystemEvents and AnomalyRecords
    by the notification service. Delivery lifecycle:
      PENDING → SENT → READ
               ↘ FAILED (retry eligible)
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_device_id", "device_id"),
        Index("ix_notifications_created_at", "created_at"),
        {"comment": "User-facing alerts generated from anomalies and system events"},
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
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    anomaly_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("anomaly_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    system_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("system_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Content ---
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ANOMALY_ALERT | BILLING_SUMMARY | DEVICE_OFFLINE | SYSTEM | etc.",
    )

    # --- Delivery ---
    channels: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'{}'",
        comment='Delivery channel config: {"in_app": true, "sms": false, "push": true}',
    )
    status: Mapped[NotificationStatus] = mapped_column(
        String(20),
        nullable=False,
        default=NotificationStatus.PENDING,
        server_default=NotificationStatus.PENDING.value,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(
        default=0, server_default="0", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Notification user={self.user_id} type={self.notification_type} "
            f"status={self.status}>"
        )
