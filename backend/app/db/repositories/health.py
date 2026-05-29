"""
app/db/repositories/health.py
=============================
Repositories for Device Health and Anomaly tracking.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.domain.enums.anomaly_type import AnomalyType
from app.domain.models.health import AnomalyRecord, DeviceHealthRecord


class DeviceHealthRepository(BaseRepository[DeviceHealthRecord]):
    """Repository for periodic device health heartbeats."""

    model = DeviceHealthRecord

    async def get_latest_health(self, device_id: uuid.UUID) -> DeviceHealthRecord | None:
        """Fetch the most recent health record for a device."""
        stmt = (
            select(DeviceHealthRecord)
            .where(DeviceHealthRecord.device_id == device_id)
            .order_by(DeviceHealthRecord.recorded_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class AnomalyRepository(BaseRepository[AnomalyRecord]):
    """Repository for lifecycle tracking of electrical and data anomalies."""

    model = AnomalyRecord

    async def get_unresolved_anomaly(
        self, device_id: uuid.UUID, anomaly_type: AnomalyType
    ) -> AnomalyRecord | None:
        """Check if an unresolved anomaly of a specific type currently exists."""
        stmt = (
            select(AnomalyRecord)
            .where(
                AnomalyRecord.device_id == device_id,
                AnomalyRecord.anomaly_type == anomaly_type,
                AnomalyRecord.is_resolved == False,  # noqa: E712
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
