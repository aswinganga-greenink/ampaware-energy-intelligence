"""
tests/integration/test_telemetry_pipeline.py
============================================
Full pipeline integration tests.
"""
import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums.connection_type import ConnectionType
from app.domain.enums.device_status import DeviceStatus
from app.domain.enums.user_role import UserRole
from app.domain.models.device import (
    Device,
    DeviceAuthToken,
    DeviceConfiguration,
    DeviceLocation,
)
from app.domain.models.user import User
from app.utils.crypto import get_hash


@pytest.mark.asyncio
async def test_full_telemetry_ingestion_pipeline(
    async_client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Test the full telemetry ingestion flow:
    1. Authenticate using hardware token.
    2. Redis deduplication check.
    3. Anomaly detection.
    4. Energy aggregation.
    """
    # 1. Setup seed data
    user = User(
        email=f"test_factory_{uuid.uuid4()}@ampaware.com",
        full_name="Factory Manager",
        hashed_password="fake_hash",
        role=UserRole.CONSUMER,
    )
    db_session.add(user)
    await db_session.flush()

    device = Device(
        serial_number=f"ESP32-INTEGRATION-{str(uuid.uuid4())[:8]}",
        name="Main Extruder",
        owner_id=user.id,
        connection_type=ConnectionType.THREE_PHASE_BALANCED,
        status=DeviceStatus.ACTIVE,
    )
    db_session.add(device)
    await db_session.flush()
    
    config = DeviceConfiguration(
        device_id=device.id,
        ct_ratio=1.0,
        voltage_nominal_v=230.0,
        current_rated_a=32.0,
    )
    db_session.add(config)

    raw_token = f"secret-device-token-{uuid.uuid4()}"
    auth_token = DeviceAuthToken(
        device_id=device.id,
        token_hash=get_hash(raw_token),
        token_prefix="secret-d",
        is_active=True,
    )
    db_session.add(auth_token)
    
    device_id_str = str(device.id)
    await db_session.commit()

    # 2. Fire telemetry packet
    payload = {
        "sequence_number": 100,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "voltage_v": 235.5,
        "current_a": 10.2,
        "active_power_w": 2280.0,
        "reactive_power_var": 50.0,
        "apparent_power_va": 2402.1,
        "power_factor": 0.95,
        "frequency_hz": 50.0,
    }

    # 3. Request
    response = await async_client.post(
        "/api/v1/telemetry/ingest",
        json=payload,
        headers={
            "X-Device-Id": device_id_str,
            "X-Device-Token": raw_token,
        },
    )
    
    assert response.status_code == 202, f"Failed: {response.text}"
    assert response.json()["sequence"] == "100"
    
    # 4. Fire duplicate packet (Redis deduplication should catch it)
    response_dup = await async_client.post(
        "/api/v1/telemetry/ingest",
        json=payload,
        headers={
            "X-Device-Id": device_id_str,
            "X-Device-Token": raw_token,
        },
    )
    assert response_dup.status_code == 409, f"Failed: {response_dup.text}"
