"""
app/db/repositories/audit.py
============================
Repositories for Audit Logs, System Events, and Notifications.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.domain.models.audit import AuditLog, Notification, SystemEvent


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for immutable system audit logs."""

    model = AuditLog


class SystemEventRepository(BaseRepository[SystemEvent]):
    """Repository for machine-readable system events."""

    model = SystemEvent


class NotificationRepository(BaseRepository[Notification]):
    """Repository for system notifications."""

    model = Notification

    async def get_pending_notifications(self, user_id: uuid.UUID) -> list[Notification]:
        """Fetch undelivered pending notifications for a user."""
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status == "PENDING",
            )
            .order_by(Notification.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
