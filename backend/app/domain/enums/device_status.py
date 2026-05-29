"""
app/domain/enums/device_status.py
===================================
Lifecycle states of a registered smart meter device.
"""
from __future__ import annotations

import enum


class DeviceStatus(str, enum.Enum):
    """
    Operational lifecycle state of a device.

    PENDING       — registered but not yet commissioned (no telemetry yet)
    ACTIVE        — commissioned and receiving telemetry
    INACTIVE      — deactivated by admin/owner (excluded from billing)
    MAINTENANCE   — temporarily offline for maintenance (excluded from alerts)
    DECOMMISSIONED — permanently retired (soft-deleted)
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"
