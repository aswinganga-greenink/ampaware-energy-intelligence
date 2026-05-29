"""
app/db/repositories/telemetry.py
================================
Repository for high-volume raw telemetry ingestion.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.domain.models.telemetry import TelemetryReading


class TelemetryRepository(BaseRepository[TelemetryReading]):
    """
    Repository for managing TelemetryReadings.
    Note: TelemetryReading is an append-only time-series model.
    It does not support soft-deletes.
    """

    model = TelemetryReading

    async def get_latest_reading(self, device_id: uuid.UUID) -> TelemetryReading | None:
        """Fetch the most recent valid telemetry reading for a device."""
        stmt = (
            select(TelemetryReading)
            .where(
                TelemetryReading.device_id == device_id,
                TelemetryReading.is_valid == True,  # noqa: E712
            )
            .order_by(TelemetryReading.recorded_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_readings_in_range(
        self, device_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[TelemetryReading]:
        """Fetch all valid readings for a device within a time range (inclusive)."""
        stmt = (
            select(TelemetryReading)
            .where(
                TelemetryReading.device_id == device_id,
                TelemetryReading.is_valid == True,  # noqa: E712
                TelemetryReading.recorded_at >= start,
                TelemetryReading.recorded_at <= end,
            )
            .order_by(TelemetryReading.recorded_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
