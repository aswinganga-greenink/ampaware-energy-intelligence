"""
app/db/repositories/__init__.py
===============================
Repository exports.
"""
from app.db.repositories.audit import (
    AuditLogRepository,
    NotificationRepository,
    SystemEventRepository,
)
from app.db.repositories.base import BaseRepository
from app.db.repositories.billing import BillingSnapshotRepository
from app.db.repositories.device import (
    DeviceAuthTokenRepository,
    DeviceConfigurationRepository,
    DeviceLocationRepository,
    DeviceRepository,
)
from app.db.repositories.energy import (
    EnergyAccumulationRepository,
    EnergyAggregateRepository,
)
from app.db.repositories.health import AnomalyRepository, DeviceHealthRepository
from app.db.repositories.tariff import (
    TariffCategoryRepository,
    TariffSlabRepository,
    TariffTodModifierRepository,
    TariffTodWindowRepository,
    TariffVersionRepository,
)
from app.db.repositories.telemetry import TelemetryRepository
from app.db.repositories.user import UserApiKeyRepository, UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "UserApiKeyRepository",
    "DeviceRepository",
    "DeviceConfigurationRepository",
    "DeviceLocationRepository",
    "DeviceAuthTokenRepository",
    "TelemetryRepository",
    "EnergyAccumulationRepository",
    "EnergyAggregateRepository",
    "TariffCategoryRepository",
    "TariffVersionRepository",
    "TariffSlabRepository",
    "TariffTodWindowRepository",
    "TariffTodModifierRepository",
    "BillingSnapshotRepository",
    "DeviceHealthRepository",
    "AnomalyRepository",
    "AuditLogRepository",
    "SystemEventRepository",
    "NotificationRepository",
]
