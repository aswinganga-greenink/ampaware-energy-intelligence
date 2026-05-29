"""
app/domain/models/energy.py
============================
Energy accumulation and aggregate models.

Tables:
  energy_accumulations      — per-reading-pair energy delta (raw accumulation)
  energy_hourly_aggregates  — pre-aggregated hourly energy buckets
  energy_daily_aggregates   — pre-aggregated daily energy + statistics
  energy_monthly_aggregates — pre-aggregated monthly totals (billing basis)

Design decisions:

1. INTERNAL UNIT: WATT-HOURS (Wh), NOT kWh.
   - Stored as NUMERIC(20, 6) — 14 integer digits, 6 decimal places.
   - 6 decimal places = precision to 1 micro-Wh (0.000001 Wh).
   - This prevents floating-point accumulation drift across millions of rows.
   - kWh = Wh / 1000 is computed only at display/billing time.
   - NUMERIC in PostgreSQL uses arbitrary-precision decimal arithmetic.

2. DELTA-TIME BASED ACCUMULATION:
   - energy_accumulations stores one row per (prev_reading, curr_reading) pair.
   - delta_seconds = curr.recorded_at - prev.recorded_at (exact, signed).
   - energy_wh = total_active_power_w * delta_seconds / 3600
   - Negative delta_seconds → out-of-order packet → skipped accumulation.
   - Very large delta (>3× expected interval) → gap detected → partial credit.

3. TOD BUCKETS:
   - Each accumulation row belongs to exactly ONE TOD bucket.
   - If a reading spans a bucket boundary (e.g., starts at 17:55, ends 18:05),
     the energy is split proportionally using linear interpolation.
   - This logic lives in the energy accumulation service (Phase 6).

4. AGGREGATE TABLES are denormalized read-optimised copies.
   - Built by APScheduler jobs: hourly (every 5 min), daily (every hour),
     monthly (once per day).
   - UNIQUE constraints enforce idempotent upserts.
   - analytics queries NEVER touch telemetry_readings directly.

5. energy_accumulations.from_telemetry_id references the PREVIOUS reading.
   - Allows gap detection: if prev → curr skip > N packets, flag as GAP.
   - from_telemetry_id is NULL for the very first reading of a device.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums.time_of_day import TimeOfDayBucket


class EnergyAccumulation(UUIDPrimaryKeyMixin, Base):
    """
    Energy delta for one telemetry reading interval.

    One row per valid (prev_reading → curr_reading) pair.
    This is the atomic unit of energy accounting.

    Invariants:
    - delta_seconds > 0 (enforced by CHECK)
    - delta_seconds < max_gap_seconds (configurable, default 3600)
      Readings after a long gap are stored with is_gap_filled=True
      and should not be counted toward energy accumulation.
    - energy_wh >= 0 (negative power loads are anomalous)
    """

    __tablename__ = "energy_accumulations"
    __table_args__ = (
        Index("ix_energy_acc_device_to_ts", "device_id", "to_recorded_at"),
        Index("ix_energy_acc_device_bucket", "device_id", "time_of_day_bucket"),
        Index("ix_energy_acc_to_telemetry_id", "to_telemetry_id"),
        CheckConstraint(
            "delta_seconds > 0",
            name="ck_energy_acc_delta_positive",
        ),
        CheckConstraint(
            "active_energy_wh >= 0",
            name="ck_energy_acc_wh_nonneg",
        ),
        {"comment": "Per-interval energy delta — atomic unit of energy accounting"},
    )

    # --- Source readings ---
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    from_telemetry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("telemetry_readings.id", ondelete="SET NULL"),
        nullable=True,
        comment="Previous reading (NULL for very first reading of a device)",
    )
    to_telemetry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("telemetry_readings.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Current reading that defines this interval",
    )

    # --- Timestamps (denormalized from telemetry for fast range queries) ---
    from_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="recorded_at of the FROM reading (NULL for first reading)",
    )
    to_recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="recorded_at of the TO reading (partition/range query key)",
    )

    # --- Delta ---
    delta_seconds: Mapped[float] = mapped_column(
        Numeric(14, 6),
        nullable=False,
        comment="Elapsed seconds between from and to readings (exact)",
    )

    # --- Energy (stored in Wh, 6 decimal places) ---
    active_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6),
        nullable=False,
        comment="P_total × delta_seconds / 3600 — stored in Wh NOT kWh",
    )

    # --- TOD classification ---
    time_of_day_bucket: Mapped[TimeOfDayBucket] = mapped_column(
        String(10),
        nullable=False,
        comment="DAY | PEAK | NIGHT — based on device timezone at to_recorded_at",
    )

    # --- Gap detection ---
    is_gap_filled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="True if delta_seconds exceeds the expected interval by > 3×",
    )
    expected_delta_seconds: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
        comment="Device's configured interval at ingestion time (for gap ratio)",
    )

    # --- Audit ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<EnergyAccumulation device={self.device_id} "
            f"wh={self.active_energy_wh} bucket={self.time_of_day_bucket}>"
        )


class EnergyHourlyAggregate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Pre-aggregated hourly energy totals per device.

    Built by APScheduler from energy_accumulations.
    UPSERT-safe: (device_id, hour_start) is unique.

    Query pattern: analytics for last 24 hours, load curves.
    """

    __tablename__ = "energy_hourly_aggregates"
    __table_args__ = (
        UniqueConstraint(
            "device_id",
            "hour_start",
            name="uq_energy_hourly_device_hour",
        ),
        Index("ix_energy_hourly_device_hour", "device_id", "hour_start"),
        {"comment": "Pre-aggregated hourly energy per device"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    hour_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="UTC timestamp of the start of the hour (truncated to 00:00 of that hour)",
    )

    # --- Energy by TOD bucket ---
    total_active_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0, comment="Total Wh this hour"
    )
    day_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0, comment="DAY bucket Wh"
    )
    peak_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0, comment="PEAK bucket Wh"
    )
    night_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0, comment="NIGHT bucket Wh"
    )

    # --- Power statistics ---
    avg_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Average active power this hour (W)"
    )
    max_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Peak active power this hour (W)"
    )
    min_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Minimum active power this hour (W)"
    )
    avg_voltage_v: Mapped[float | None] = mapped_column(
        Numeric(9, 4), nullable=True, comment="Average voltage this hour (V)"
    )
    avg_power_factor: Mapped[float | None] = mapped_column(
        Numeric(6, 5), nullable=True
    )

    # --- Metadata ---
    reading_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of valid readings this hour"
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="True once the hour has fully elapsed (locked for modification)",
    )


class EnergyDailyAggregate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Pre-aggregated daily energy totals per device.

    'date' is in the device's LOCAL timezone (not UTC) so that
    midnight-to-midnight billing periods are meaningful for the consumer.
    """

    __tablename__ = "energy_daily_aggregates"
    __table_args__ = (
        UniqueConstraint(
            "device_id",
            "date",
            name="uq_energy_daily_device_date",
        ),
        Index("ix_energy_daily_device_date", "device_id", "date"),
        {"comment": "Pre-aggregated daily energy in device local timezone"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Local date (in device timezone) — NOT UTC date",
    )

    # --- Energy totals ---
    total_active_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0
    )
    day_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0
    )
    peak_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0
    )
    night_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0
    )

    # --- Statistics ---
    avg_active_power_w: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    max_active_power_w: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    avg_voltage_v: Mapped[float | None] = mapped_column(Numeric(9, 4), nullable=True)
    avg_current_a: Mapped[float | None] = mapped_column(Numeric(9, 5), nullable=True)
    avg_power_factor: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)
    min_power_factor: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)

    # --- Data quality ---
    reading_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_intervals_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of expected intervals with no data",
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="True once the day has fully elapsed",
    )
    gap_filled_wh: Mapped[float] = mapped_column(
        Numeric(20, 6),
        nullable=False,
        default=0,
        comment="Energy from gap-filled intervals (may be less accurate)",
    )


class EnergyMonthlyAggregate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Pre-aggregated monthly energy totals per device.

    This is the primary basis for billing calculations.
    year+month are in the device's local timezone.

    UNIQUE on (device_id, year, month) ensures exactly one row per
    device per billing month.
    """

    __tablename__ = "energy_monthly_aggregates"
    __table_args__ = (
        UniqueConstraint(
            "device_id",
            "year",
            "month",
            name="uq_energy_monthly_device_year_month",
        ),
        Index("ix_energy_monthly_device_ym", "device_id", "year", "month"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_energy_monthly_month_range"),
        CheckConstraint("year >= 2020 AND year <= 2100", name="ck_energy_monthly_year_range"),
        {"comment": "Monthly energy totals per device — primary billing basis"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False, comment="1–12")

    # --- Energy totals ---
    total_active_energy_wh: Mapped[float] = mapped_column(
        Numeric(20, 6), nullable=False, default=0, comment="Total month Wh"
    )
    day_energy_wh: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False, default=0)
    peak_energy_wh: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False, default=0)
    night_energy_wh: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False, default=0)

    # --- Derived (computed at billing time, stored for display) ---
    total_active_energy_kwh: Mapped[float | None] = mapped_column(
        Numeric(14, 6),
        nullable=True,
        comment="total_active_energy_wh / 1000 — stored for convenience",
    )

    # --- Statistics ---
    avg_active_power_w: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    max_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Peak demand this month"
    )
    avg_power_factor: Mapped[float | None] = mapped_column(Numeric(6, 5), nullable=True)

    # --- Data quality ---
    reading_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Days with no data"
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="True once the calendar month has elapsed",
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the monthly aggregate was locked for billing",
    )
