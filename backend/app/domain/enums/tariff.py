"""
app/domain/enums/tariff.py
============================
Tariff classification enums for KSEB billing categories.
"""
from __future__ import annotations

import enum


class TariffCategoryCode(str, enum.Enum):
    """
    KSEB tariff category codes.

    LT = Low Tension (residential/small commercial, <11 kV)
    HT = High Tension (large industrial, 11 kV and above)

    These map directly to KSEB's published tariff schedule.
    New categories can be added to the DB without code changes.
    """

    LT_DOMESTIC = "LT_DOMESTIC"           # residential, 1-phase or 3-phase < 500 units
    LT_COMMERCIAL = "LT_COMMERCIAL"       # shops, offices
    LT_INDUSTRIAL = "LT_INDUSTRIAL"       # factories on LT supply
    LT_AGRICULTURE = "LT_AGRICULTURE"     # agricultural pump sets
    HT_INDUSTRIAL = "HT_INDUSTRIAL"       # large industry on HT supply
    HT_COMMERCIAL = "HT_COMMERCIAL"       # large commercial on HT supply


class BillingSnapshotType(str, enum.Enum):
    """
    What the billing snapshot represents.

    PROJECTED_TODAY   — running estimate for today
    PROJECTED_MONTH   — running estimate for the current billing month
    FINAL_MONTHLY     — locked final bill for a completed month
    CUSTOM            — arbitrary date range
    """

    PROJECTED_TODAY = "PROJECTED_TODAY"
    PROJECTED_MONTH = "PROJECTED_MONTH"
    FINAL_MONTHLY = "FINAL_MONTHLY"
    CUSTOM = "CUSTOM"


class SystemEventType(str, enum.Enum):
    """Structured system events written to system_events table."""

    DEVICE_REGISTERED = "DEVICE_REGISTERED"
    DEVICE_ONLINE = "DEVICE_ONLINE"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    DEVICE_DECOMMISSIONED = "DEVICE_DECOMMISSIONED"
    TARIFF_CREATED = "TARIFF_CREATED"
    TARIFF_UPDATED = "TARIFF_UPDATED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    ANOMALY_RESOLVED = "ANOMALY_RESOLVED"
    BILLING_SNAPSHOT_CREATED = "BILLING_SNAPSHOT_CREATED"
    FIRMWARE_UPDATED = "FIRMWARE_UPDATED"
    USER_CREATED = "USER_CREATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    MIGRATION_APPLIED = "MIGRATION_APPLIED"


class NotificationStatus(str, enum.Enum):
    """Delivery lifecycle of a notification."""

    PENDING = "PENDING"
    SENT = "SENT"
    READ = "READ"
    FAILED = "FAILED"


class AuditAction(str, enum.Enum):
    """Database-level audit log action types."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SOFT_DELETE = "SOFT_DELETE"
    RESTORE = "RESTORE"
