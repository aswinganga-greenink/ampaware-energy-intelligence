"""
app/services/anomaly.py
=======================
Service for tracking and evaluating electrical and data anomalies.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.health import AnomalyRepository
from app.domain.enums.anomaly_type import AnomalySeverity, AnomalyType
from app.domain.models.health import AnomalyRecord
from app.domain.models.telemetry import TelemetryReading


class AnomalyService:
    """Service handling anomaly detection and lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.anomaly_repo = AnomalyRepository(session)

    async def evaluate_telemetry_for_anomalies(self, reading: TelemetryReading) -> None:
        """
        Evaluate a telemetry reading against electrical safety thresholds.
        If thresholds are breached, open an anomaly (if one isn't already open).
        If thresholds are normalized, resolve any currently open anomalies.
        """
        # Thresholds (in a real system, these would be loaded from DeviceConfiguration)
        VOLTAGE_HIGH = 250.0
        VOLTAGE_LOW = 190.0
        POWER_FACTOR_LOW = 0.6

        # Check Overvoltage
        if reading.voltage_v > VOLTAGE_HIGH:
            await self._trigger_anomaly(
                device_id=reading.device_id,
                anomaly_type=AnomalyType.OVER_VOLTAGE,
                severity=AnomalySeverity.HIGH,
                description=f"Voltage breached upper threshold: {reading.voltage_v}V",
                extra_data={"voltage_v": float(reading.voltage_v), "threshold": VOLTAGE_HIGH},
            )
        else:
            await self._resolve_anomaly_if_open(
                device_id=reading.device_id,
                anomaly_type=AnomalyType.OVER_VOLTAGE,
                resolve_reason="Voltage returned to normal operational limits.",
            )

        # Check Undervoltage
        if reading.voltage_v < VOLTAGE_LOW:
            await self._trigger_anomaly(
                device_id=reading.device_id,
                anomaly_type=AnomalyType.UNDER_VOLTAGE,
                severity=AnomalySeverity.MEDIUM,
                description=f"Voltage breached lower threshold: {reading.voltage_v}V",
                extra_data={"voltage_v": float(reading.voltage_v), "threshold": VOLTAGE_LOW},
            )
        else:
            await self._resolve_anomaly_if_open(
                device_id=reading.device_id,
                anomaly_type=AnomalyType.UNDER_VOLTAGE,
                resolve_reason="Voltage returned to normal operational limits.",
            )

        # Check Power Factor
        if reading.power_factor < POWER_FACTOR_LOW:
            await self._trigger_anomaly(
                device_id=reading.device_id,
                anomaly_type=AnomalyType.LOW_POWER_FACTOR,
                severity=AnomalySeverity.MEDIUM,
                description=f"Power factor critically low: {reading.power_factor}",
                extra_data={
                    "power_factor": float(reading.power_factor),
                    "threshold": POWER_FACTOR_LOW,
                },
            )
        else:
            await self._resolve_anomaly_if_open(
                device_id=reading.device_id,
                anomaly_type=AnomalyType.LOW_POWER_FACTOR,
                resolve_reason="Power factor normalized.",
            )

    async def _trigger_anomaly(
        self,
        device_id: uuid.UUID,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        description: str,
        extra_data: dict,
    ) -> AnomalyRecord:
        """Create a new anomaly if one of the same type isn't already active."""
        existing = await self.anomaly_repo.get_unresolved_anomaly(
            device_id, anomaly_type
        )
        if existing:
            # Optionally update the severity or extra_data, but here we just leave it active
            return existing

        anomaly = AnomalyRecord(
            device_id=device_id,
            anomaly_type=anomaly_type,
            severity=severity,
            detected_at=datetime.now(timezone.utc),
            description=description,
            extra_data=extra_data,
        )
        return await self.anomaly_repo.create(anomaly)

    async def _resolve_anomaly_if_open(
        self,
        device_id: uuid.UUID,
        anomaly_type: AnomalyType,
        resolve_reason: str,
    ) -> None:
        """Close an active anomaly when conditions normalize."""
        existing = await self.anomaly_repo.get_unresolved_anomaly(
            device_id, anomaly_type
        )
        if existing:
            existing.is_resolved = True
            existing.resolved_at = datetime.now(timezone.utc)
            existing.resolution_notes = resolve_reason
            await self.anomaly_repo.update(existing)
