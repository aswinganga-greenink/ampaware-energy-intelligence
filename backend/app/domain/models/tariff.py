"""
app/domain/models/tariff.py
============================
KSEB tariff schema — completely separated from energy engine.

Tables:
  tariff_categories    — LT Domestic, LT Commercial, etc.
  tariff_versions      — versioned tariff with effective date range
  tariff_slabs         — slab-rate tiers within a tariff version
  tariff_tod_windows   — configurable TOD time windows per tariff version
  tariff_tod_modifiers — pricing multipliers per TOD bucket

Design decisions:

1. SEPARATION FROM ENERGY ENGINE:
   - The tariff engine ONLY consumes energy data (kWh, TOD buckets).
   - It never touches power calculations or telemetry directly.
   - All tariff logic is parameterised through DB rows, not code constants.

2. VERSIONED TARIFFS:
   - Each KSEB tariff revision is a new TariffVersion with:
     effective_from = the gazette notification date
     effective_to   = day before the next version takes effect (NULL = current)
   - Mid-month tariff changes are handled by splitting the billing period.
     Example: if tariff changes on July 15, the bill engine:
     a) Calculates Jul 1–14 using old tariff version
     b) Calculates Jul 15–31 using new tariff version
     c) Adds the two sub-bills together

3. SLAB RATES:
   - Slabs are ordered by slab_order (1, 2, 3...).
   - units_from and units_to define the inclusive range [from, to).
   - Last slab has units_to = NULL (unbounded upper limit).
   - Example KSEB LT Domestic (approximate):
     Slab 1: 0–50 units  → ₹3.15/unit
     Slab 2: 51–100 units → ₹4.70/unit
     Slab 3: 101–150 units → ₹5.80/unit
     Slab 4: 151–200 units → ₹7.00/unit
     Slab 5: 201+ units   → ₹7.50/unit

4. TOD MODIFIERS:
   - Applied as a multiplier on the energy rate for peak pricing.
   - A multiplier of 1.0 means no premium/discount.
   - Stored per tariff version so they evolve with the tariff.

5. TOD WINDOWS:
   - Time windows (when DAY/PEAK/NIGHT start/end) are stored in DB
     so they can be changed without a code deployment.
   - Evaluated server-side in the device's local timezone.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums.tariff import TariffCategoryCode
from app.domain.enums.time_of_day import TimeOfDayBucket


class TariffCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Top-level tariff classification (e.g., LT Domestic, LT Commercial).

    New categories can be added without code changes — the billing engine
    resolves the correct category via the device's tariff_category_id.
    """

    __tablename__ = "tariff_categories"
    __table_args__ = (
        Index("ix_tariff_categories_code", "code", unique=True),
        {"comment": "KSEB tariff categories (LT Domestic, LT Commercial, etc.)"},
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Machine-readable code matching TariffCategoryCode enum",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name (e.g., 'LT Domestic')",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    # --- Relationships ---
    versions: Mapped[list["TariffVersion"]] = relationship(
        "TariffVersion",
        back_populates="category",
        order_by="TariffVersion.effective_from",
    )

    def __repr__(self) -> str:
        return f"<TariffCategory code={self.code!r} name={self.name!r}>"


class TariffVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A specific tariff revision with effective date range.

    UNIQUE on (category_id, version_number).
    effective_to = NULL means this is the currently active version.
    Only one version per category should have effective_to = NULL.

    All monetary amounts are in Indian Rupees (INR).
    """

    __tablename__ = "tariff_versions"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "version_number",
            name="uq_tariff_versions_cat_version",
        ),
        Index("ix_tariff_versions_category_effective", "category_id", "effective_from"),
        Index("ix_tariff_versions_effective_to", "effective_to"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="ck_tariff_version_date_range",
        ),
        CheckConstraint(
            "fixed_charge_per_month >= 0",
            name="ck_tariff_version_fixed_charge_nonneg",
        ),
        CheckConstraint(
            "fuel_surcharge_percent >= 0 AND fuel_surcharge_percent <= 100",
            name="ck_tariff_version_fuel_surcharge_range",
        ),
        CheckConstraint(
            "electricity_duty_percent >= 0 AND electricity_duty_percent <= 100",
            name="ck_tariff_version_duty_range",
        ),
        {"comment": "Versioned tariff rates with gazette effective dates"},
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tariff_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential version number within a category (1, 2, 3...)",
    )

    # --- Date range ---
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="First day this tariff applies (inclusive)",
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Last day this tariff applies (inclusive). NULL = currently active",
    )

    # --- Fixed charges ---
    fixed_charge_per_month: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        default=0,
        comment="Fixed monthly meter rent + service charge in INR",
    )

    # --- Percentage-based surcharges (applied to energy charges) ---
    fuel_surcharge_percent: Mapped[float] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=0,
        comment="KSEB fuel cost adjustment surcharge (% of energy charges)",
    )
    electricity_duty_percent: Mapped[float] = mapped_column(
        Numeric(7, 4),
        nullable=False,
        default=0,
        comment="State electricity duty (% of energy charges)",
    )

    # --- Optional TOD support ---
    has_tod_pricing: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="Whether TOD modifiers apply to this tariff version",
    )

    # --- Audit ---
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reference to gazette notification or official circular",
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin user who entered this tariff version",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    # --- Relationships ---
    category: Mapped["TariffCategory"] = relationship(
        "TariffCategory", back_populates="versions"
    )
    slabs: Mapped[list["TariffSlab"]] = relationship(
        "TariffSlab",
        back_populates="tariff_version",
        order_by="TariffSlab.slab_order",
        cascade="all, delete-orphan",
    )
    tod_modifiers: Mapped[list["TariffTodModifier"]] = relationship(
        "TariffTodModifier",
        back_populates="tariff_version",
        cascade="all, delete-orphan",
    )
    tod_windows: Mapped[list["TariffTodWindow"]] = relationship(
        "TariffTodWindow",
        back_populates="tariff_version",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TariffVersion cat={self.category_id} v={self.version_number} "
            f"from={self.effective_from} to={self.effective_to}>"
        )


class TariffSlab(UUIDPrimaryKeyMixin, Base):
    """
    A single rate slab within a tariff version.

    Slabs partition the total unit consumption into tiers.
    The billing engine applies each slab rate only to the portion of
    consumption falling within that tier.

    Example for 175 units under KSEB LT Domestic:
      Slab 1 (0–50):   50 × ₹3.15 = ₹157.50
      Slab 2 (51–100): 50 × ₹4.70 = ₹235.00
      Slab 3 (101–150): 50 × ₹5.80 = ₹290.00
      Slab 4 (151–200): 25 × ₹7.00 = ₹175.00
      Total energy charge = ₹857.50
    """

    __tablename__ = "tariff_slabs"
    __table_args__ = (
        UniqueConstraint(
            "tariff_version_id",
            "slab_order",
            name="uq_tariff_slabs_version_order",
        ),
        Index("ix_tariff_slabs_version", "tariff_version_id"),
        CheckConstraint("slab_order >= 1", name="ck_tariff_slab_order_positive"),
        CheckConstraint("units_from >= 0", name="ck_tariff_slab_units_from_nonneg"),
        CheckConstraint(
            "units_to IS NULL OR units_to > units_from",
            name="ck_tariff_slab_units_range",
        ),
        CheckConstraint("rate_per_unit >= 0", name="ck_tariff_slab_rate_nonneg"),
        {"comment": "Rate slabs within a tariff version (kWh tiers)"},
    )

    tariff_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tariff_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    slab_order: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1-based ordering of slabs"
    )
    units_from: Mapped[float] = mapped_column(
        Numeric(10, 3),
        nullable=False,
        comment="Start of slab in kWh (inclusive)",
    )
    units_to: Mapped[float | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
        comment="End of slab in kWh (exclusive). NULL = unbounded (last slab)",
    )
    rate_per_unit: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="INR per kWh for consumption within this slab",
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- Relationship ---
    tariff_version: Mapped["TariffVersion"] = relationship(
        "TariffVersion", back_populates="slabs"
    )

    def __repr__(self) -> str:
        return (
            f"<TariffSlab order={self.slab_order} "
            f"[{self.units_from}–{self.units_to}] ₹{self.rate_per_unit}/kWh>"
        )


class TariffTodWindow(UUIDPrimaryKeyMixin, Base):
    """
    Configurable time-of-day window boundaries per tariff version.

    Stores when each TOD bucket starts and ends (in local time).
    Allows changing peak hours (e.g., from 18:00–22:00 to 17:00–23:00)
    via a tariff version update without any code change.
    """

    __tablename__ = "tariff_tod_windows"
    __table_args__ = (
        UniqueConstraint(
            "tariff_version_id",
            "bucket",
            name="uq_tariff_tod_windows_version_bucket",
        ),
        Index("ix_tariff_tod_windows_version", "tariff_version_id"),
        {"comment": "Time-of-day window boundaries per tariff version (local time)"},
    )

    tariff_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tariff_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    bucket: Mapped[TimeOfDayBucket] = mapped_column(
        String(10),
        nullable=False,
        comment="DAY | PEAK | NIGHT",
    )
    window_start: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Local time when this bucket starts (e.g., 18:00 for PEAK)",
    )
    window_end: Mapped[time] = mapped_column(
        Time,
        nullable=False,
        comment="Local time when this bucket ends (e.g., 22:00 for PEAK)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tariff_version: Mapped["TariffVersion"] = relationship(
        "TariffVersion", back_populates="tod_windows"
    )


class TariffTodModifier(UUIDPrimaryKeyMixin, Base):
    """
    Rate multiplier per TOD bucket per tariff version.

    Multiplier examples:
      DAY   = 1.00  (no premium — baseline rate)
      PEAK  = 1.20  (20% premium over slab rate during peak hours)
      NIGHT = 0.85  (15% discount during off-peak night hours)

    A multiplier of 1.0 for all buckets = no TOD pricing.
    """

    __tablename__ = "tariff_tod_modifiers"
    __table_args__ = (
        UniqueConstraint(
            "tariff_version_id",
            "bucket",
            name="uq_tariff_tod_modifiers_version_bucket",
        ),
        CheckConstraint(
            "multiplier > 0 AND multiplier <= 5.0",
            name="ck_tariff_tod_modifier_multiplier_range",
        ),
        {"comment": "TOD pricing multipliers per tariff version"},
    )

    tariff_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tariff_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    bucket: Mapped[TimeOfDayBucket] = mapped_column(
        String(10), nullable=False, comment="DAY | PEAK | NIGHT"
    )
    multiplier: Mapped[float] = mapped_column(
        Numeric(6, 4),
        nullable=False,
        default=1.0,
        comment="Rate multiplier (1.0 = no change, 1.2 = 20% surcharge)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tariff_version: Mapped["TariffVersion"] = relationship(
        "TariffVersion", back_populates="tod_modifiers"
    )

    def __repr__(self) -> str:
        return f"<TariffTodModifier bucket={self.bucket} mult={self.multiplier}>"
