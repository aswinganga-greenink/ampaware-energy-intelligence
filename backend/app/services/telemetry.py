"""
app/services/telemetry.py
=========================
Business logic for telemetry ingestion, deduplication, and bounds checking.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicatePacketError
from app.db.repositories.device import DeviceRepository
from app.db.repositories.telemetry import TelemetryRepository
from app.domain.models.telemetry import TelemetryReading
from app.domain.schemas.telemetry import TelemetryIngestPayload
from app.infrastructure.redis.client import redis_client, redis_key


class TelemetryService:
    """Service handling telemetry ingestion logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.device_repo = DeviceRepository(session)
        self.telemetry_repo = TelemetryRepository(session)

    async def ingest_payload(
        self,
        device_id: uuid.UUID,
        payload: TelemetryIngestPayload,
        raw_payload_json: dict,
    ) -> TelemetryReading:
        """
        Ingest a raw telemetry payload.

        Steps:
        1. Deduplication check via Redis (sliding window/setnx).
        2. Validate electrical bounds.
        3. Persist TelemetryReading.
        """
        # 1. Deduplication via Redis SETNX
        # Using device_id + sequence_number guarantees exactly-once processing per sequence
        dedup_key = redis_key(
            "telemetry", "dedup", str(device_id), str(payload.sequence_number)
        )
        # setnx returns True if the key was set (i.e. it did not exist).
        is_new = await redis_client.setnx(dedup_key, "1")
        if not is_new:
            raise DuplicatePacketError(
                "Duplicate telemetry sequence detected.",
                device_id=str(device_id),
                sequence=payload.sequence_number,
            )

        # Retain deduplication memory for 24 hours (prevents redis memory leak)
        await redis_client.expire(dedup_key, 86400)

        # 2. Electrical bounds validation (strict constraints)
        is_valid = True
        validation_errors = []

        # Assuming a nominal 230V system, limits might be 180V-260V.
        if payload.voltage_v < 180 or payload.voltage_v > 260:
            is_valid = False
            validation_errors.append(f"Voltage out of bounds: {payload.voltage_v}V")

        if payload.power_factor < 0.5:
            is_valid = False
            validation_errors.append(
                f"Critically low power factor: {payload.power_factor}"
            )

        if payload.frequency_hz < 48 or payload.frequency_hz > 52:
            is_valid = False
            validation_errors.append(
                f"Grid frequency out of bounds: {payload.frequency_hz}Hz"
            )

        # 3. Persistence
        reading = TelemetryReading(
            device_id=device_id,
            sequence_number=payload.sequence_number,
            recorded_at=payload.recorded_at,
            received_at=datetime.now(timezone.utc),
            voltage_v=payload.voltage_v,
            current_a=payload.current_a,
            active_power_w=payload.active_power_w,
            reactive_power_var=payload.reactive_power_var,
            apparent_power_va=payload.apparent_power_va,
            power_factor=payload.power_factor,
            frequency_hz=payload.frequency_hz,
            is_valid=is_valid,
            validation_errors=validation_errors if not is_valid else None,
            raw_payload=raw_payload_json,
        )

        return await self.telemetry_repo.create(reading)
