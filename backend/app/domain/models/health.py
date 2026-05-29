"""
app/domain/models/health.py
============================
Device health and anomaly detection models.

Tables:
  device_health_records — periodic health snapshots (heartbeat data)
  anomaly_records       — detected electrical and data quality anomalies
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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums.anomaly_type import AnomalySeverity, AnomalyType


class DeviceHealthRecord(UUIDPrimaryKeyMixin, Base):
    """
    Periodic health snapshot from a device.

    Written by the health monitor service on every heartbeat check.
    Append-only — not updated.

    Contains both connectivity status (from the server's perspective)
    and embedded device diagnostics (from the ESP32 firmware telemetry).

    Query patterns:
    - Latest health status per device: (device_id, recorded_at DESC) LIMIT 1
    - Historical uptime: aggregate over time range
    - Offline detection: WHERE is_online = FALSE AND recorded_at > cutoff
    """

    __tablename__ = "device_health_records"
    __table_args__ = (
        Index("ix_device_health_device_recorded", "device_id", "recorded_at"),
        Index("ix_device_health_is_online", "is_online"),
        {"comment": "Periodic device health snapshots (heartbeat + diagnostics)"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this health check was performed",
    )

    # --- Connectivity ---
    is_online: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        comment="True if device sent telemetry within the expected interval",
    )
    last_telemetry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the most recent valid telemetry packet",
    )
    seconds_since_last_telemetry: Mapped[float | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
        comment="Seconds elapsed since last valid packet (used for alert thresholding)",
    )

    # --- ESP32 diagnostics (from embedded firmware metadata) ---
    firmware_version: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Firmware version reported by device"
    )
    wifi_rssi_dbm: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="WiFi signal strength in dBm (e.g., -70 = good, -90 = poor)",
    )
    free_heap_bytes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="ESP32 free heap memory in bytes",
    )
    cpu_temperature_c: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="ESP32 internal temperature sensor in °C",
    )
    uptime_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Device uptime since last reset in seconds",
    )
    reset_reason: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="ESP32 reset reason (POWER_ON, WATCHDOG, PANIC, etc.)",
    )

    # --- Telemetry rate ---
    packets_last_hour: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of telemetry packets received in the last 60 minutes",
    )
    expected_packets_last_hour: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Expected packet count based on configured interval",
    )

    # --- Derived health score (0–100) ---
    health_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment=(
            "Composite health score 0–100. "
            "100 = fully healthy, 0 = completely offline/failed. "
            "Factors: online status, packet rate, RSSI, heap, anomalies"
        ),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<DeviceHealthRecord device={self.device_id} "
            f"online={self.is_online} score={self.health_score}>"
        )


class AnomalyRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A detected electrical or data-quality anomaly.

    Anomalies are created by the health monitoring engine (Phase 11)
    and resolved by admin action or automatic recovery detection.

    Invariants:
    - detected_at <= resolved_at (if resolved)
    - is_resolved == (resolved_at IS NOT NULL)
    - metric_value and threshold_value stored for reproducibility
      (thresholds may change after detection; store the value that triggered)

    Phase classification:
    - phase = 'A', 'B', 'C' for phase-specific anomalies
    - phase = NULL for total/system-level anomalies (outage, clock drift, etc.)
    """

    __tablename__ = "anomaly_records"
    __table_args__ = (
        Index("ix_anomaly_device_detected", "device_id", "detected_at"),
        Index("ix_anomaly_type_severity", "anomaly_type", "severity"),
        Index("ix_anomaly_is_resolved", "is_resolved"),
        Index("ix_anomaly_device_unresolved", "device_id", "is_resolved"),
        CheckConstraint(
            "resolved_at IS NULL OR resolved_at >= detected_at",
            name="ck_anomaly_resolved_after_detected",
        ),
        CheckConstraint(
            "phase IS NULL OR phase IN ('A', 'B', 'C')",
            name="ck_anomaly_phase_valid",
        ),
        {"comment": "Detected electrical and data quality anomalies"},
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    telemetry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("telemetry_readings.id", ondelete="SET NULL"),
        nullable=True,
        comment="The triggering telemetry reading (if applicable)",
    )

    # --- Classification ---
    anomaly_type: Mapped[AnomalyType] = mapped_column(
        String(50), nullable=False, comment="Type from AnomalyType enum"
    )
    severity: Mapped[AnomalySeverity] = mapped_column(
        String(20), nullable=False, comment="LOW | MEDIUM | HIGH | CRITICAL"
    )
    phase: Mapped[str | None] = mapped_column(
        String(1),
        nullable=True,
        comment="'A', 'B', 'C' for phase-specific; NULL for system-level",
    )

    # --- Timing ---
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the anomaly was first detected",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the anomaly resolved (auto or manual)",
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Numeric(14, 3),
        nullable=True,
        comment="Computed duration (resolved_at - detected_at)",
    )

    # --- Values (frozen at detection time) ---
    metric_value: Mapped[float | None] = mapped_column(
        Numeric(16, 6),
        nullable=True,
        comment="The actual sensor value that triggered the anomaly",
    )
    threshold_value: Mapped[float | None] = mapped_column(
        Numeric(16, 6),
        nullable=True,
        comment="The threshold value at detection time",
    )
    metric_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Unit of measurement (V, A, %, W, etc.)",
    )

    # --- State ---
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    auto_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True if resolved automatically by the system",
    )

    # --- Narrative ---
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Human-readable description of the anomaly",
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Notes entered when resolving the anomaly"
    )

    # --- Metadata ---
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional context (e.g., all 3 phase values at detection time)",
    )
    acknowledged_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who acknowledged this anomaly",
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", lazy="select")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<AnomalyRecord device={self.device_id} "
            f"type={self.anomaly_type} severity={self.severity} "
            f"resolved={self.is_resolved}>"
        )
