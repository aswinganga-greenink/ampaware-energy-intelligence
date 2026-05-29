"""
app/domain/models/telemetry.py
================================
Raw telemetry ingestion model.

Table: telemetry_readings

Design decisions:
- This is the highest-volume table in the system.
  At 10-second intervals across 10,000 devices:
  → 1 device = 8,640 rows/day
  → 10,000 devices = 86,400,000 rows/day (~1B rows/year)

  Mitigation strategy:
  1. Partition by recorded_at (month-level range partitioning).
     Create new partitions monthly via APScheduler job.
  2. Index on (device_id, recorded_at DESC) — primary query pattern.
  3. Raw payload in JSONB for full auditability without schema migration.
  4. Computed power values stored at ingestion time for fast reads.
  5. Retention policy: raw readings kept 90 days; energy aggregates kept forever.

- NO soft delete: telemetry is an append-only audit log.
  Invalid readings are marked is_valid=False with flags, never deleted.

- recorded_at = device's timestamp (from ESP32 RTC).
  received_at = server's timestamp.
  The delta between them reveals clock drift.

- All electrical values use NUMERIC (not FLOAT) to avoid accumulation
  of floating-point errors over millions of rows.

- Phase fields:
  Single phase: phase_a_* only
  3-phase balanced: phase_a_* used as the per-phase value (all phases equal)
  3-phase unbalanced: all three phase_* columns populated

- sequence_number: monotonically increasing counter from the device.
  Used for detecting out-of-order or missing packets even when timestamps
  are unreliable due to clock drift.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums.connection_type import ConnectionType


class TelemetryReading(Base):
    """
    Raw telemetry packet from an ESP32 smart meter.

    Append-only: never updated or deleted (only is_valid flag may be set).
    Partitioned by recorded_at for efficient time-range queries.
    """

    __tablename__ = "telemetry_readings"
    __table_args__ = (
        # Primary query: latest N readings for a device
        Index(
            "ix_telemetry_device_recorded",
            "device_id",
            "recorded_at",
        ),
        # Detect clock drift: compare recorded vs received
        Index("ix_telemetry_received_at", "received_at"),
        # Filter invalid readings
        Index("ix_telemetry_is_valid", "is_valid"),
        # Sequence number for gap/out-of-order detection
        Index("ix_telemetry_device_seq", "device_id", "sequence_number"),
        # CHECK: power factor must be in [-1, 1] range
        CheckConstraint(
            "phase_a_power_factor IS NULL OR "
            "(phase_a_power_factor >= -1.0 AND phase_a_power_factor <= 1.0)",
            name="ck_telemetry_pf_a_range",
        ),
        CheckConstraint(
            "phase_b_power_factor IS NULL OR "
            "(phase_b_power_factor >= -1.0 AND phase_b_power_factor <= 1.0)",
            name="ck_telemetry_pf_b_range",
        ),
        CheckConstraint(
            "phase_c_power_factor IS NULL OR "
            "(phase_c_power_factor >= -1.0 AND phase_c_power_factor <= 1.0)",
            name="ck_telemetry_pf_c_range",
        ),
        # Voltage must be non-negative (0 = phase lost, not negative)
        CheckConstraint(
            "phase_a_voltage IS NULL OR phase_a_voltage >= 0",
            name="ck_telemetry_voltage_a_nonneg",
        ),
        CheckConstraint(
            "phase_b_voltage IS NULL OR phase_b_voltage >= 0",
            name="ck_telemetry_voltage_b_nonneg",
        ),
        CheckConstraint(
            "phase_c_voltage IS NULL OR phase_c_voltage >= 0",
            name="ck_telemetry_voltage_c_nonneg",
        ),
        {"comment": "Raw telemetry readings from ESP32 smart meters (append-only)"},
    )

    # --- Primary key ---
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Immutable row identifier",
    )

    # --- Device reference ---
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Source device — RESTRICT prevents orphan deletion",
    )

    # --- Timestamps ---
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Device-local timestamp (from ESP32 RTC) — partition key",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Server receipt timestamp — delta vs recorded_at reveals clock drift",
    )

    # --- Packet sequencing ---
    sequence_number: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Monotonic counter from device firmware for gap detection",
    )

    # --- Connection type (denormalized for query efficiency) ---
    connection_type: Mapped[ConnectionType] = mapped_column(
        String(50),
        nullable=False,
        comment="Copied from device at ingestion time (avoids join on hot path)",
    )

    # ---------------------------------------------------------------
    # Raw sensor values — NUMERIC to prevent floating-point drift
    # ---------------------------------------------------------------

    # Phase A (always populated)
    phase_a_voltage: Mapped[float | None] = mapped_column(
        Numeric(9, 4),
        nullable=True,
        comment="Phase A (or single phase) RMS voltage in Volts",
    )
    phase_a_current: Mapped[float | None] = mapped_column(
        Numeric(9, 5),
        nullable=True,
        comment="Phase A RMS current in Amperes",
    )
    phase_a_power_factor: Mapped[float | None] = mapped_column(
        Numeric(6, 5),
        nullable=True,
        comment="Phase A power factor [-1.0, +1.0]. Negative = leading (capacitive)",
    )

    # Phase B (three-phase only)
    phase_b_voltage: Mapped[float | None] = mapped_column(
        Numeric(9, 4), nullable=True, comment="Phase B RMS voltage in Volts"
    )
    phase_b_current: Mapped[float | None] = mapped_column(
        Numeric(9, 5), nullable=True, comment="Phase B RMS current in Amperes"
    )
    phase_b_power_factor: Mapped[float | None] = mapped_column(
        Numeric(6, 5), nullable=True, comment="Phase B power factor [-1.0, +1.0]"
    )

    # Phase C (three-phase only)
    phase_c_voltage: Mapped[float | None] = mapped_column(
        Numeric(9, 4), nullable=True, comment="Phase C RMS voltage in Volts"
    )
    phase_c_current: Mapped[float | None] = mapped_column(
        Numeric(9, 5), nullable=True, comment="Phase C RMS current in Amperes"
    )
    phase_c_power_factor: Mapped[float | None] = mapped_column(
        Numeric(6, 5), nullable=True, comment="Phase C power factor [-1.0, +1.0]"
    )

    # ---------------------------------------------------------------
    # Computed power values (stored at ingestion — never recomputed)
    # Stored to avoid recalculation on every analytics query.
    # If calibration changes, affected readings can be reprocessed
    # and stored in a separate reprocessed_power table.
    # ---------------------------------------------------------------

    # Phase A computed
    phase_a_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="P_A = V_A × I_A × PF_A (Watts)"
    )
    phase_a_apparent_power_va: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="S_A = V_A × I_A (VA)"
    )
    phase_a_reactive_power_var: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Q_A = √(S_A² - P_A²) (VAR)"
    )

    # Phase B computed
    phase_b_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="P_B (Watts)"
    )
    phase_b_apparent_power_va: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="S_B (VA)"
    )
    phase_b_reactive_power_var: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Q_B (VAR)"
    )

    # Phase C computed
    phase_c_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="P_C (Watts)"
    )
    phase_c_apparent_power_va: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="S_C (VA)"
    )
    phase_c_reactive_power_var: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Q_C (VAR)"
    )

    # Total (sum of all phases)
    total_active_power_w: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="P_total = P_A + P_B + P_C (Watts)"
    )
    total_apparent_power_va: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="S_total (VA)"
    )
    total_reactive_power_var: Mapped[float | None] = mapped_column(
        Numeric(14, 4), nullable=True, comment="Q_total (VAR)"
    )
    total_power_factor: Mapped[float | None] = mapped_column(
        Numeric(6, 5),
        nullable=True,
        comment="Weighted average PF across all phases",
    )

    # ---------------------------------------------------------------
    # Data quality flags
    # ---------------------------------------------------------------

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="False if any validation rule rejected this reading",
    )
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True if this packet was identified as a duplicate of another",
    )
    is_out_of_order: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True if this packet arrived after a later-timestamped packet",
    )
    validation_flags: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment=(
            "Machine-readable validation failure details. "
            'Example: {"voltage_out_of_range": {"phase": "A", "value": 280.5}}'
        ),
    )

    # --- Original payload (audit) ---
    raw_payload: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Original JSON payload from the device for forensic replay",
    )

    # --- Server metadata ---
    ingest_latency_ms: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Milliseconds between received_at and storage commit",
    )

    # Timestamp only (no updated_at — append-only)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    device: Mapped["Device"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Device",
        lazy="select",
        foreign_keys=[device_id],
    )

    def __repr__(self) -> str:
        return (
            f"<TelemetryReading id={self.id} device={self.device_id} "
            f"recorded={self.recorded_at} valid={self.is_valid}>"
        )
