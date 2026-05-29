"""
app/domain/models/__init__.py
==============================
Central model registry.

IMPORTANT: This file MUST import every ORM model class so that:
1. SQLAlchemy's mapper registry is fully populated before any query runs.
2. Alembic's autogenerate finds all tables via Base.metadata.
3. Relationship back_populates resolve correctly across modules.

Add new models here as each phase introduces them.
"""
from app.domain.models.audit import AuditLog, Notification, SystemEvent
from app.domain.models.billing import BillingSnapshot
from app.domain.models.device import (
    Device,
    DeviceAuthToken,
    DeviceConfiguration,
    DeviceLocation,
)
from app.domain.models.energy import (
    EnergyAccumulation,
    EnergyDailyAggregate,
    EnergyHourlyAggregate,
    EnergyMonthlyAggregate,
)
from app.domain.models.health import AnomalyRecord, DeviceHealthRecord
from app.domain.models.tariff import (
    TariffCategory,
    TariffSlab,
    TariffTodModifier,
    TariffTodWindow,
    TariffVersion,
)
from app.domain.models.telemetry import TelemetryReading
from app.domain.models.user import User, UserApiKey

__all__ = [
    # Users
    "User",
    "UserApiKey",
    # Devices
    "Device",
    "DeviceConfiguration",
    "DeviceLocation",
    "DeviceAuthToken",
    # Telemetry
    "TelemetryReading",
    # Energy
    "EnergyAccumulation",
    "EnergyHourlyAggregate",
    "EnergyDailyAggregate",
    "EnergyMonthlyAggregate",
    # Tariff
    "TariffCategory",
    "TariffVersion",
    "TariffSlab",
    "TariffTodWindow",
    "TariffTodModifier",
    # Billing
    "BillingSnapshot",
    # Health & Anomaly
    "DeviceHealthRecord",
    "AnomalyRecord",
    # Audit & Events
    "AuditLog",
    "SystemEvent",
    "Notification",
]
