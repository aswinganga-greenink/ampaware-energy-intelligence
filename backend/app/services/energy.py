"""
app/services/energy.py
======================
Service for energy accumulation and idempotent time-series aggregation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.energy import (
    EnergyAccumulationRepository,
    EnergyAggregateRepository,
)
from app.domain.enums.time_of_day import TimeOfDayBucket
from app.domain.models.energy import EnergyAccumulation
from app.domain.models.telemetry import TelemetryReading
from app.utils.datetime_utils import floor_to_day, floor_to_hour, is_same_day_utc


class EnergyAggregationService:
    """Service to crunch raw telemetry into energy deltas and time buckets."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.accumulation_repo = EnergyAccumulationRepository(session)
        self.aggregate_repo = EnergyAggregateRepository(session)

    def determine_tod_bucket(self, dt: datetime) -> TimeOfDayBucket:
        """
        Classify a timestamp into a KSEB Time-of-Day bucket.
        KSEB TOD (Typical):
        - NORMAL (DAY): 06:00 - 18:00
        - PEAK: 18:00 - 22:00
        - OFF_PEAK (NIGHT): 22:00 - 06:00
        """
        from app.utils.datetime_utils import to_ist

        ist_dt = to_ist(dt)
        hour = ist_dt.hour

        if 6 <= hour < 18:
            return TimeOfDayBucket.DAY
        elif 18 <= hour < 22:
            return TimeOfDayBucket.PEAK
        else:
            return TimeOfDayBucket.NIGHT

    async def process_telemetry_to_energy(
        self, current_reading: TelemetryReading
    ) -> None:
        """
        Calculates the exact Wh (Watt-hours) consumed since the last reading,
        then atomically upserts the hourly, daily, and monthly aggregates.
        """
        bucket = self.determine_tod_bucket(current_reading.recorded_at)

        # 1. Fetch previous accumulation for this bucket/device
        latest_acc = await self.accumulation_repo.get_latest_accumulation(
            current_reading.device_id, bucket
        )

        # Calculate Delta Energy
        delta_kwh = 0.0
        if latest_acc:
            # Time difference in hours
            time_diff_hours = (
                current_reading.recorded_at - latest_acc.to_recorded_at
            ).total_seconds() / 3600.0

            if time_diff_hours > 0:
                # Average Power Method (Trapezoidal integration for higher accuracy)
                avg_power_w = (
                    float(current_reading.active_power_w)
                    + float(latest_acc.to_active_power_w)
                ) / 2.0

                # Delta kWh = (Avg Power in W * hours) / 1000
                delta_kwh = (avg_power_w * time_diff_hours) / 1000.0

                # Prevent negative energy accumulation from drift/noise
                if delta_kwh < 0:
                    delta_kwh = 0.0

        # 2. Store the new accumulation marker
        new_acc = EnergyAccumulation(
            device_id=current_reading.device_id,
            time_of_day_bucket=bucket,
            from_recorded_at=latest_acc.to_recorded_at
            if latest_acc
            else current_reading.recorded_at,
            to_recorded_at=current_reading.recorded_at,
            from_telemetry_id=latest_acc.to_telemetry_id
            if latest_acc
            else current_reading.id,
            to_telemetry_id=current_reading.id,
            delta_kwh=delta_kwh,
            to_active_power_w=current_reading.active_power_w,
        )
        await self.accumulation_repo.create(new_acc)

        # If no energy was consumed, skip aggregate UPSERTs to save DB load
        if delta_kwh == 0.0:
            return

        # 3. Categorize kWh for aggregates
        day_kwh = delta_kwh if bucket == TimeOfDayBucket.DAY else 0.0
        peak_kwh = delta_kwh if bucket == TimeOfDayBucket.PEAK else 0.0
        night_kwh = delta_kwh if bucket == TimeOfDayBucket.NIGHT else 0.0

        # 4. UPSERT Hourly Aggregate
        hour_start = floor_to_hour(current_reading.recorded_at)
        await self.aggregate_repo.upsert_hourly_aggregate(
            device_id=current_reading.device_id,
            hour_start=hour_start,
            delta_kwh=delta_kwh,
            day_kwh=day_kwh,
            peak_kwh=peak_kwh,
            night_kwh=night_kwh,
        )

        # 5. UPSERT Daily Aggregate
        day_start = floor_to_day(current_reading.recorded_at).date()
        await self.aggregate_repo.upsert_daily_aggregate(
            device_id=current_reading.device_id,
            target_date=day_start,
            delta_kwh=delta_kwh,
            day_kwh=day_kwh,
            peak_kwh=peak_kwh,
            night_kwh=night_kwh,
        )

        # 6. UPSERT Monthly Aggregate
        # We use IST year/month for billing alignment
        from app.utils.datetime_utils import to_ist

        ist_dt = to_ist(current_reading.recorded_at)

        await self.aggregate_repo.upsert_monthly_aggregate(
            device_id=current_reading.device_id,
            year=ist_dt.year,
            month=ist_dt.month,
            delta_kwh=delta_kwh,
            day_kwh=day_kwh,
            peak_kwh=peak_kwh,
            night_kwh=night_kwh,
        )
