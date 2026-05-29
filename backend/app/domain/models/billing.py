"""
app/domain/models/billing.py
==============================
Billing snapshot model.

Table: billing_snapshots

Design decisions:
- A billing snapshot is a complete, point-in-time bill calculation.
- Both projected (mid-month estimate) and final (end-of-month locked) bills
  are snapshots — distinguished by is_projected and snapshot_type.
- The full slab-level breakdown is stored as JSONB so the consumer can
  see exactly how their bill was calculated, even after tariff changes.
- All monetary values in INR to 4 decimal places.
- tariff_version_id references the SPECIFIC version used — if the tariff
  changes mid-month, two snapshots are created (one per version) and merged
  into the final bill.
- Snapshots are NEVER mutated after finalization (is_finalized=True).
  A new snapshot is created for recalculations (e.g., after a meter correction).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums.tariff import BillingSnapshotType


class BillingSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Immutable bill computation result.

    Projected snapshots are regenerated daily.
    Final monthly snapshots are created once per month and locked.

    Invariants:
    - billing_period_start <= billing_period_end
    - All energy fields >= 0
    - total_payable >= 0
    - Once is_finalized = True, the row must NOT be mutated
      (create a correction_of_id chain instead)
    """

    __tablename__ = "billing_snapshots"
    __table_args__ = (
        Index("ix_billing_device_period", "device_id", "billing_period_start"),
        Index("ix_billing_device_type", "device_id", "snapshot_type"),
        Index("ix_billing_owner_period", "owner_id", "billing_period_start"),
        Index("ix_billing_is_projected", "is_projected"),
        CheckConstraint(
            "billing_period_end >= billing_period_start",
            name="ck_billing_period_valid",
        ),
        CheckConstraint("total_units_kwh >= 0", name="ck_billing_units_nonneg"),
        CheckConstraint("total_payable >= 0", name="ck_billing_payable_nonneg"),
        {"comment": "Complete billing calculation snapshots (projected + final)"},
    )

    # --- Ownership ---
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Denormalized from device for direct consumer queries",
    )
    tariff_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tariff_versions.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Tariff version used for this specific billing calculation",
    )

    # --- Billing period ---
    billing_period_start: Mapped[date] = mapped_column(
        Date, nullable=False, comment="First day of the billing period (inclusive)"
    )
    billing_period_end: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Last day of the billing period (inclusive)"
    )

    # --- Type ---
    snapshot_type: Mapped[BillingSnapshotType] = mapped_column(
        String(30),
        nullable=False,
        comment="PROJECTED_TODAY | PROJECTED_MONTH | FINAL_MONTHLY | CUSTOM",
    )
    is_projected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="True = estimate, False = locked final bill",
    )
    is_finalized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True = immutable, do not modify",
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Energy quantities (stored in kWh for billing display) ---
    total_units_kwh: Mapped[float] = mapped_column(
        Numeric(14, 6),
        nullable=False,
        comment="Total kWh consumed in the billing period",
    )
    day_units_kwh: Mapped[float] = mapped_column(
        Numeric(14, 6), nullable=False, default=0, comment="DAY bucket kWh"
    )
    peak_units_kwh: Mapped[float] = mapped_column(
        Numeric(14, 6), nullable=False, default=0, comment="PEAK bucket kWh"
    )
    night_units_kwh: Mapped[float] = mapped_column(
        Numeric(14, 6), nullable=False, default=0, comment="NIGHT bucket kWh"
    )

    # --- Bill components (INR, 4 decimal places) ---
    energy_charge_inr: Mapped[float] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        comment="Sum of all slab charges before surcharges",
    )
    fixed_charge_inr: Mapped[float] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=0,
        comment="Monthly fixed charge (pro-rated if period < full month)",
    )
    fuel_surcharge_inr: Mapped[float] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=0,
        comment="Fuel cost adjustment surcharge",
    )
    electricity_duty_inr: Mapped[float] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=0,
        comment="State electricity duty",
    )
    total_payable_inr: Mapped[float] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        comment="Final payable amount including all charges and taxes",
    )

    # --- Audit & traceability ---
    breakdown: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment=(
            "Full slab-by-slab breakdown for audit. "
            "Structure: {slabs: [{order, units_from, units_to, units, rate, charge}], "
            "tod_modifiers: {...}, surcharges: {...}}"
        ),
    )

    # --- Correction chain ---
    correction_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("billing_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        comment="If this snapshot corrects a previous one, reference the original",
    )
    correction_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Reason for correction (e.g., 'CT ratio recalibrated')"
    )

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", lazy="select")  # type: ignore[name-defined]  # noqa: F821
    owner: Mapped["User"] = relationship("User", lazy="select")  # type: ignore[name-defined]  # noqa: F821
    tariff_version: Mapped["TariffVersion"] = relationship("TariffVersion", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<BillingSnapshot device={self.device_id} "
            f"period={self.billing_period_start}–{self.billing_period_end} "
            f"₹{self.total_payable_inr} projected={self.is_projected}>"
        )
