"""
app/api/deps.py
===============
FastAPI dependency injection module.
"""
from __future__ import annotations

import uuid
from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DeviceAuthenticationError
from app.db.repositories.device import DeviceAuthTokenRepository, DeviceRepository
from app.db.session import get_db_session
from app.domain.models.device import Device
from app.services.anomaly import AnomalyService
from app.services.energy import EnergyAggregationService
from app.services.telemetry import TelemetryService
from app.utils.crypto import get_hash


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional DB session for a request."""
    async for session in get_db_session():
        yield session


# --- Services ---

def get_telemetry_service(session: AsyncSession = Depends(get_db)) -> TelemetryService:
    return TelemetryService(session)


def get_anomaly_service(session: AsyncSession = Depends(get_db)) -> AnomalyService:
    return AnomalyService(session)


def get_energy_service(session: AsyncSession = Depends(get_db)) -> EnergyAggregationService:
    return EnergyAggregationService(session)


# --- Authentication ---

async def get_device_token(
    x_device_id: uuid.UUID = Header(..., description="Device UUID"),
    x_device_token: str = Header(..., description="Pre-shared device token"),
    session: AsyncSession = Depends(get_db),
) -> Device:
    """
    Authenticate a hardware device using its pre-shared token.
    Used exclusively for high-volume IoT ingestion routes.
    """
    token_repo = DeviceAuthTokenRepository(session)
    device_repo = DeviceRepository(session)
    
    token_hash = get_hash(x_device_token)
    
    # Check if the token is valid for this device
    valid_token = await token_repo.get_active_auth_token(
        device_id=x_device_id, token_hash=token_hash
    )
    
    if not valid_token:
        raise DeviceAuthenticationError("Invalid or expired device token.")
        
    # Get the actual device (with configuration eager-loaded)
    device = await device_repo.get_with_config_and_location(x_device_id)
    if not device:
        raise DeviceAuthenticationError("Device not found or inactive.")
        
    return device


from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.exceptions import TokenInvalidError, TokenExpiredError
from app.domain.models.user import User
from app.db.repositories.user import UserRepository

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().api_v1_prefix}/auth/login"
)

async def get_current_user(
    session: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    """
    Dependency to authenticate a User via JWT.
    Validates token signature and expiration, then loads the User from DB.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt.algorithm]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise TokenInvalidError("Subject (sub) missing from token.")
            
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise TokenInvalidError("Subject (sub) is not a valid UUID.")
            
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired.")
    except (JWTError, ValidationError):
        raise TokenInvalidError("Invalid access token.")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise TokenInvalidError("User associated with this token no longer exists.")
    if not user.is_active:
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("User account is disabled.")

    return user

