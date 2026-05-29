"""
app/api/v1/endpoints/dashboard.py
=================================
User dashboard and analytics summary API.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.repositories.device import DeviceRepository
from app.domain.models.user import User

router = APIRouter(tags=["dashboard"])


@router.get(
    "/summary",
    summary="Get user dashboard summary metrics",
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns high-level analytics for the user's dashboard.
    - Total active devices
    - Total energy consumption (Wh) for current month
    - Active anomalies
    """
    device_repo = DeviceRepository(session)
    
    # 1. Get user's devices
    user_devices = await device_repo.get_devices_by_owner(current_user.id)
    device_ids = [device.id for device in user_devices]
    
    total_active_devices = sum(1 for d in user_devices if d.is_online)
    
    # Return simple metrics for initial V1 integration
    return {
        "metrics": {
            "total_devices": len(device_ids),
            "active_devices": total_active_devices,
        }
    }
