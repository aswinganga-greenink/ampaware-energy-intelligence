"""
app/domain/models/device.py
============================
Device registration and configuration ORM models.

Tables:
  devices                 — registered ESP32 smart meter units
  device_configurations   — calibration and operational settings per device
  device_locations        — installation address and GPS coordinates
  device_auth_tokens      — per-device authentication credentials

Design decisions:
- serial_number is the device's factory-assigned unique ID (ESP32 chip ID).
  It is the trust anchor for device authentication.
- connection_type on the device record determines which telemetry schema
  to expect and which power calculation formula to apply.
- Device configuration is a 1:1 relation (one active config per device).
  Historical configs are NOT soft-deleted — they are superseded.
  This matters for billing: we need to know what calibration was active
  when a given reading was taken.
- device_auth_tokens are separate from JWTs — devices use pre-shared keys
  embedded in firmware, not user JWTs. They can be rotated remotely.
- Timezone is stored per-device because industrial sites may span timezones.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, FullAuditMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums.connection_type import ConnectionType
from app.domain.enums.device_status import DeviceStatus


class Device(FullAuditMixin, Base):
    """
    Registered smart meter device.

    Invariants:
    - serial_number is globally unique across all devices.
    - Only ACTIVE devices accept telemetry ingestion.
    - Timezone defaults to 'Asia/Kolkata' for Kerala deployments
      but must be explicitly set for non-IST installations.
    """

    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_serial_number", "serial_number", unique=True),
        Index("ix_devices_owner_id", "owner_id"),
        Index("ix_devices_status", "status"),
        Index("ix_devices_connection_type", "connection_type"),
        Index("ix_devices_last_seen_at", "last_seen_at"),
        Index("ix_devices_owner_status", "owner_id", "status"),
        {"comment": "Registered ESP32 smart meter units"},
    )

    # --- Identity ---
    serial_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="ESP32 factory-assigned unique ID (trust anchor for auth)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable label (e.g., 'Main Panel', 'Kitchen Circuit')",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about the installation",
    )

    # --- Ownership ---
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who owns/manages this device",
    )

    # --- Electrical configuration ---
    connection_type: Mapped[ConnectionType] = mapped_column(
        String(50),
        nullable=False,
        comment="SINGLE_PHASE | THREE_PHASE_BALANCED | THREE_PHASE_UNBALANCED",
    )

    # --- Operational state ---
    status: Mapped[DeviceStatus] = mapped_column(
        String(30),
        nullable=False,
        default=DeviceStatus.PENDING,
        server_default=DeviceStatus.PENDING.value,
        comment="Lifecycle state of the device",
    )
    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="Updated by health monitor heartbeat checks",
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of last received telemetry packet",
    )
    commissioned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when device moved to ACTIVE status",
    )

    # --- Firmware ---
    firmware_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Semantic version of installed firmware (e.g., '2.1.4')",
    )
    hardware_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="PCB revision (e.g., 'rev3.0')",
    )

    # --- Locale ---
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Asia/Kolkata",
        server_default="'Asia/Kolkata'",
        comment="IANA timezone (e.g., 'Asia/Kolkata') for TOD classification",
    )

    # --- Metadata ---
    tags: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Arbitrary key-value tags for grouping/filtering (e.g., building, floor)",
    )

    # --- Relationships ---
    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="devices",
        foreign_keys=[owner_id],
    )
    configuration: Mapped["DeviceConfiguration | None"] = relationship(
        "DeviceConfiguration",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
    )
    location: Mapped["DeviceLocation | None"] = relationship(
        "DeviceLocation",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
    )
    auth_token: Mapped["DeviceAuthToken | None"] = relationship(
        "DeviceAuthToken",
        back_populates="device",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Device id={self.id} serial={self.serial_number!r} "
            f"status={self.status} conn={self.connection_type}>"
        )


class DeviceConfiguration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Per-device calibration and operational configuration.

    One-to-one with Device.  When configuration changes (e.g., CT ratio
    recalibrated on site), the old record is updated (with updated_at
    reflecting the change). The telemetry row stores the raw sensor values;
    the power calculation engine reads the active config at computation time.

    Calibration fields:
    - ct_ratio: Current Transformer turns ratio (e.g., 100:5 → ct_ratio=20).
      Applied as a multiplier to the raw current reading from the ADC.
    - pt_ratio: Potential Transformer ratio (usually 1 for LT installations).
    - calibration_factor: Additional site-specific correction factor.
      Allows fine-tuning post-installation to match utility meter readings.
    """

    __tablename__ = "device_configurations"
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_device_configurations_device_id"),
        CheckConstraint("ct_ratio > 0", name="ck_device_config_ct_ratio_positive"),
        CheckConstraint("pt_ratio > 0", name="ck_device_config_pt_ratio_positive"),
        CheckConstraint(
            "calibration_factor > 0 AND calibration_factor <= 10",
            name="ck_device_config_calibration_factor_range",
        ),
        CheckConstraint(
            "telemetry_interval_seconds >= 1 AND telemetry_interval_seconds <= 3600",
            name="ck_device_config_interval_range",
        ),
        {"comment": "Calibration and operational configuration for each device"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- Tariff association ---
    tariff_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tariff_categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="Which tariff category applies to this installation",
    )

    # --- Electrical parameters ---
    voltage_nominal_v: Mapped[float] = mapped_column(
        Numeric(8, 3),
        nullable=False,
        default=230.0,
        comment="Nominal line voltage in Volts (230 for LT domestic, 415 for 3-phase)",
    )
    current_rated_a: Mapped[float] = mapped_column(
        Numeric(8, 3),
        nullable=False,
        default=32.0,
        comment="Rated current capacity of the installation in Amperes",
    )

    # --- Calibration ---
    ct_ratio: Mapped[float] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=1.0,
        comment="Current transformer ratio (raw_current × ct_ratio = actual_current)",
    )
    pt_ratio: Mapped[float] = mapped_column(
        Numeric(12, 6),
        nullable=False,
        default=1.0,
        comment="Potential transformer ratio (usually 1 for LT)",
    )
    calibration_factor: Mapped[float] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=1.0,
        comment="Site-specific correction factor (1.0 = no correction)",
    )

    # --- Telemetry settings ---
    telemetry_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        comment="Expected seconds between telemetry packets from this device",
    )
    max_missing_packets_before_alert: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=6,
        comment="How many consecutive missed packets trigger an offline alert",
    )

    # --- Thresholds for anomaly detection ---
    voltage_high_threshold_v: Mapped[float] = mapped_column(
        Numeric(8, 3),
        nullable=False,
        default=253.0,
        comment="Upper voltage limit in Volts (110% of 230V nominal)",
    )
    voltage_low_threshold_v: Mapped[float] = mapped_column(
        Numeric(8, 3),
        nullable=False,
        default=207.0,
        comment="Lower voltage limit in Volts (90% of 230V nominal)",
    )
    power_factor_low_threshold: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.85,
        comment="Alert when power factor drops below this value",
    )
    current_high_threshold_a: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
        comment="Overcurrent alert threshold (defaults to current_rated_a × 1.1 if NULL)",
    )
    phase_imbalance_threshold_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=10.0,
        comment="Alert when any phase differs from average by more than this %",
    )

    # --- Relationship ---
    device: Mapped["Device"] = relationship(
        "Device",
        back_populates="configuration",
    )
    tariff_category: Mapped["TariffCategory | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "TariffCategory",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<DeviceConfiguration device={self.device_id} "
            f"ct={self.ct_ratio} interval={self.telemetry_interval_seconds}s>"
        )


class DeviceLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Physical installation address and GPS coordinates.

    Stored separately from Device to keep the hot-path device table lean.
    Location is queried infrequently (admin views, maps).
    """

    __tablename__ = "device_locations"
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_device_locations_device_id"),
        Index("ix_device_locations_pincode", "pincode"),
        {"comment": "Physical installation location for each device"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # --- Address ---
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Kerala"
    )
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(
        String(100), nullable=False, default="India"
    )

    # --- GPS ---
    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="WGS84 latitude",
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
        comment="WGS84 longitude",
    )

    # --- Installation metadata ---
    installation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    installed_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the installing technician",
    )
    installed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Relationship ---
    device: Mapped["Device"] = relationship("Device", back_populates="location")


class DeviceAuthToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Pre-shared authentication key embedded in device firmware.

    Devices authenticate using HMAC-SHA256 of their payload signed with
    this token.  Tokens can be rotated via admin API without re-flashing.

    Security:
    - Only the SHA-256 hash of the token is stored; the plaintext is
      shown to the admin ONCE at creation time.
    - token_prefix (first 8 chars) is stored for identification.
    - expires_at: NULL = never expires (typical for embedded devices).
    """

    __tablename__ = "device_auth_tokens"
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_device_auth_tokens_device_id"),
        Index("ix_device_auth_tokens_token_hash", "token_hash", unique=True),
        {"comment": "Pre-shared HMAC keys for ESP32 device authentication"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="SHA-256 of the raw pre-shared key",
    )
    token_prefix: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        comment="First 8 chars of the raw key for identification",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when this token replaced a previous one",
    )

    # --- Relationship ---
    device: Mapped["Device"] = relationship("Device", back_populates="auth_token")

    def __repr__(self) -> str:
        return (
            f"<DeviceAuthToken device={self.device_id} "
            f"prefix={self.token_prefix!r} active={self.is_active}>"
        )
