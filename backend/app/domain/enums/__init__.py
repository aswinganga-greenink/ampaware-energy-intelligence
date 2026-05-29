"""
app/domain/enums/__init__.py
=============================
Re-export all domain enums for convenient single-import access.

Usage:
    from app.domain.enums import ConnectionType, DeviceStatus, UserRole
"""
from app.domain.enums.anomaly_type import AnomalySeverity, AnomalyType
from app.domain.enums.connection_type import ConnectionType
from app.domain.enums.device_status import DeviceStatus
from app.domain.enums.tariff import (
    AuditAction,
    BillingSnapshotType,
    NotificationStatus,
    SystemEventType,
    TariffCategoryCode,
)
from app.domain.enums.time_of_day import TimeOfDayBucket
from app.domain.enums.user_role import UserRole

__all__ = [
    "AnomalySeverity",
    "AnomalyType",
    "AuditAction",
    "BillingSnapshotType",
    "ConnectionType",
    "DeviceStatus",
    "NotificationStatus",
    "SystemEventType",
    "TariffCategoryCode",
    "TimeOfDayBucket",
    "UserRole",
]
