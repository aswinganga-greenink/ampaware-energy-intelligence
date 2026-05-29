"""
app/db/repositories/device.py
=============================
Device, Configuration, Location, and AuthToken repositories.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.domain.enums.device_status import DeviceStatus
from app.domain.models.device import (
    Device,
    DeviceAuthToken,
    DeviceConfiguration,
    DeviceLocation,
)


class DeviceRepository(BaseRepository[Device]):
    """Repository for managing smart meter Devices."""

    model = Device

    async def get_by_serial(self, serial_number: str) -> Device | None:
        """Fetch an active device by its unique serial number."""
        stmt = select(Device).where(
            Device.serial_number == serial_number,
            Device.is_deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_config_and_location(self, device_id: uuid.UUID) -> Device | None:
        """Fetch a device eager-loading its 1-to-1 configuration and location."""
        stmt = (
            select(Device)
            .options(
                selectinload(Device.configuration),
                selectinload(Device.location),
            )
            .where(
                Device.id == device_id,
                Device.is_deleted == False,  # noqa: E712
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class DeviceConfigurationRepository(BaseRepository[DeviceConfiguration]):
    """Repository for managing Device Configurations."""

    model = DeviceConfiguration


class DeviceLocationRepository(BaseRepository[DeviceLocation]):
    """Repository for managing Device Locations."""

    model = DeviceLocation


class DeviceAuthTokenRepository(BaseRepository[DeviceAuthToken]):
    """Repository for managing Device Auth Tokens."""

    model = DeviceAuthToken

    async def get_active_auth_token(
        self, device_id: uuid.UUID, token_hash: str
    ) -> DeviceAuthToken | None:
        """
        Fetch a valid device auth token by its hash.
        A token is valid if not revoked and belongs to the given device.
        """
        stmt = select(DeviceAuthToken).where(
            DeviceAuthToken.device_id == device_id,
            DeviceAuthToken.token_hash == token_hash,
            DeviceAuthToken.is_revoked == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
