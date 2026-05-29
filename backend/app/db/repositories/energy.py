"""
app/db/repositories/energy.py
=============================
Energy Accumulation and Aggregate repositories.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.repositories.base import BaseRepository
from app.domain.enums.time_of_day import TimeOfDayBucket
from app.domain.models.energy import (
    EnergyAccumulation,
    EnergyDailyAggregate,
    EnergyHourlyAggregate,
    EnergyMonthlyAggregate,
)


class EnergyAccumulationRepository(BaseRepository[EnergyAccumulation]):
    """Repository for raw energy delta accumulations."""

    model = EnergyAccumulation

    async def get_latest_accumulation(
        self, device_id: uuid.UUID, bucket: TimeOfDayBucket
    ) -> EnergyAccumulation | None:
        """Fetch the most recent accumulation log for a device and TOD bucket."""
        stmt = (
            select(EnergyAccumulation)
            .where(
                EnergyAccumulation.device_id == device_id,
                EnergyAccumulation.time_of_day_bucket == bucket,
            )
            .order_by(EnergyAccumulation.to_recorded_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class EnergyAggregateRepository:
    """
    Combined repository for hourly, daily, and monthly aggregates.
    Note: Does not extend BaseRepository since it manages multiple models,
    and aggregates are largely UPSERT-driven time-series summaries.
    """

    def __init__(self, session):
        self._session = session

    async def upsert_hourly_aggregate(
        self,
        device_id: uuid.UUID,
        hour_start: datetime,
        delta_kwh: float,
        day_kwh: float,
        peak_kwh: float,
        night_kwh: float,
    ) -> None:
        """
        Idempotent UPSERT for hourly aggregates. If the hour row exists, 
        adds to the existing KWh values atomically.
        """
        stmt = insert(EnergyHourlyAggregate).values(
            device_id=device_id,
            hour_start=hour_start,
            total_kwh=delta_kwh,
            day_kwh=day_kwh,
            peak_kwh=peak_kwh,
            night_kwh=night_kwh,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["device_id", "hour_start"],
            set_={
                "total_kwh": EnergyHourlyAggregate.total_kwh + stmt.excluded.total_kwh,
                "day_kwh": EnergyHourlyAggregate.day_kwh + stmt.excluded.day_kwh,
                "peak_kwh": EnergyHourlyAggregate.peak_kwh + stmt.excluded.peak_kwh,
                "night_kwh": EnergyHourlyAggregate.night_kwh + stmt.excluded.night_kwh,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await self._session.execute(stmt)

    async def upsert_daily_aggregate(
        self,
        device_id: uuid.UUID,
        target_date: date,
        delta_kwh: float,
        day_kwh: float,
        peak_kwh: float,
        night_kwh: float,
    ) -> None:
        """Idempotent UPSERT for daily aggregates."""
        stmt = insert(EnergyDailyAggregate).values(
            device_id=device_id,
            date=target_date,
            total_kwh=delta_kwh,
            day_kwh=day_kwh,
            peak_kwh=peak_kwh,
            night_kwh=night_kwh,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["device_id", "date"],
            set_={
                "total_kwh": EnergyDailyAggregate.total_kwh + stmt.excluded.total_kwh,
                "day_kwh": EnergyDailyAggregate.day_kwh + stmt.excluded.day_kwh,
                "peak_kwh": EnergyDailyAggregate.peak_kwh + stmt.excluded.peak_kwh,
                "night_kwh": EnergyDailyAggregate.night_kwh + stmt.excluded.night_kwh,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await self._session.execute(stmt)

    async def upsert_monthly_aggregate(
        self,
        device_id: uuid.UUID,
        year: int,
        month: int,
        delta_kwh: float,
        day_kwh: float,
        peak_kwh: float,
        night_kwh: float,
    ) -> None:
        """Idempotent UPSERT for monthly aggregates."""
        stmt = insert(EnergyMonthlyAggregate).values(
            device_id=device_id,
            year=year,
            month=month,
            total_kwh=delta_kwh,
            day_kwh=day_kwh,
            peak_kwh=peak_kwh,
            night_kwh=night_kwh,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["device_id", "year", "month"],
            set_={
                "total_kwh": EnergyMonthlyAggregate.total_kwh + stmt.excluded.total_kwh,
                "day_kwh": EnergyMonthlyAggregate.day_kwh + stmt.excluded.day_kwh,
                "peak_kwh": EnergyMonthlyAggregate.peak_kwh + stmt.excluded.peak_kwh,
                "night_kwh": EnergyMonthlyAggregate.night_kwh + stmt.excluded.night_kwh,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        await self._session.execute(stmt)

    async def get_hourly_in_range(
        self, device_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[EnergyHourlyAggregate]:
        """Fetch hourly aggregates in time range."""
        stmt = (
            select(EnergyHourlyAggregate)
            .where(
                EnergyHourlyAggregate.device_id == device_id,
                EnergyHourlyAggregate.hour_start >= start,
                EnergyHourlyAggregate.hour_start <= end,
            )
            .order_by(EnergyHourlyAggregate.hour_start.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_daily_in_range(
        self, device_id: uuid.UUID, start: date, end: date
    ) -> list[EnergyDailyAggregate]:
        """Fetch daily aggregates in time range."""
        stmt = (
            select(EnergyDailyAggregate)
            .where(
                EnergyDailyAggregate.device_id == device_id,
                EnergyDailyAggregate.date >= start,
                EnergyDailyAggregate.date <= end,
            )
            .order_by(EnergyDailyAggregate.date.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_monthly_in_range(
        self, device_id: uuid.UUID, start_year: int, start_month: int, end_year: int, end_month: int
    ) -> list[EnergyMonthlyAggregate]:
        """Fetch monthly aggregates in time range."""
        stmt = (
            select(EnergyMonthlyAggregate)
            .where(
                EnergyMonthlyAggregate.device_id == device_id,
                (EnergyMonthlyAggregate.year * 12 + EnergyMonthlyAggregate.month) >= (start_year * 12 + start_month),
                (EnergyMonthlyAggregate.year * 12 + EnergyMonthlyAggregate.month) <= (end_year * 12 + end_month),
            )
            .order_by(EnergyMonthlyAggregate.year.asc(), EnergyMonthlyAggregate.month.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
