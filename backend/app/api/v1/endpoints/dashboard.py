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
    from app.db.repositories.telemetry import TelemetryRepository
    
    device_repo = DeviceRepository(session)
    telemetry_repo = TelemetryRepository(session)
    
    # 1. Get user's devices
    user_devices = await device_repo.get_devices_by_owner(current_user.id)
    device_ids = [device.id for device in user_devices]
    total_active_devices = sum(1 for d in user_devices if d.is_online)
    
    # 2. Get latest telemetry for the first active device (as an aggregate example)
    live_metrics = {
        "v": 0.0,
        "a": 0.0,
        "w": 0,
        "pf": 0.0,
        "kwh": 0.0,
        "devices": total_active_devices
    }
    
    if device_ids:
        latest_reading = await telemetry_repo.get_latest_reading(device_ids[0])
        if latest_reading:
            live_metrics = {
                "v": float(latest_reading.phase_a_voltage or 0),
                "a": float(latest_reading.phase_a_current or 0),
                "w": int(latest_reading.total_active_power_w or 0),
                "pf": float(latest_reading.total_power_factor or 0),
                "kwh": 142.6, # Placeholder until Energy aggregates are fully synced
                "devices": total_active_devices
            }
    
    return {
        "metrics": {
            "total_devices": len(device_ids),
            "active_devices": total_active_devices,
            "live": live_metrics
        }
    }


@router.get(
    "/billing",
    summary="Get user dashboard billing projections",
)
async def get_dashboard_billing(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Returns projected billing information for the current cycle.
    """
    # 1. Fetch user's devices
    device_repo = DeviceRepository(session)
    user_devices = await device_repo.get_devices_by_owner(current_user.id)
    device_ids = [d.id for d in user_devices]
    
    # Normally we would fetch the EnergyMonthlyAggregate for the current month
    # and pass it through the TariffEngineService. 
    # For initial integration, we'll implement the deterministic logic directly
    # here to ensure the frontend gets valid data if the database isn't seeded yet.
    
    # Assume 192 kWh consumed
    total_kwh = 192.0
    
    # Standard KSEB LT-1A slabs
    fallback_slabs = [
        {"range": "0–50", "rate": 3.15, "limit": 50},
        {"range": "51–100", "rate": 3.70, "limit": 50},
        {"range": "101–150", "rate": 4.80, "limit": 50},
        {"range": "151–200", "rate": 6.40, "limit": 50},
        {"range": "201–250", "rate": 7.60, "limit": 50},
    ]
    
    slabs_breakdown = []
    remaining_kwh = total_kwh
    subtotal = 0.0
    
    for slab in fallback_slabs:
        if remaining_kwh <= 0:
            break
            
        units_in_slab = min(remaining_kwh, slab["limit"])
        amount = units_in_slab * slab["rate"]
        
        slabs_breakdown.append({
            "range": slab["range"],
            "rate": f"₹{slab['rate']:.2f}",
            "units": round(units_in_slab, 1),
            "amount": round(amount, 2)
        })
        
        subtotal += amount
        remaining_kwh -= units_in_slab
        
    duty = subtotal * 0.10
    fixed_charge = 65.0
    total = subtotal + duty + fixed_charge
    
    # Create forecast data points
    cycle_days = []
    for i in range(30):
        actual = (total_kwh / 30) * (i + 1) if i < 15 else None # Assume we are halfway
        forecast = (total_kwh / 30) * (i + 1)
        cycle_days.append({
            "d": i + 1,
            "actual": round(actual, 1) if actual is not None else None,
            "forecast": round(forecast, 1)
        })
    
    return {
        "consumed_kwh": total_kwh,
        "cycle_days": 30,
        "avg_per_day": round(total_kwh / 30, 1),
        "slabs": slabs_breakdown,
        "subtotal": round(subtotal, 2),
        "duty": round(duty, 2),
        "fixed_charge": fixed_charge,
        "total": round(total, 2),
        "chart_data": cycle_days
    }


@router.get(
    "/devices",
    summary="Get user dashboard devices",
)
async def get_dashboard_devices(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Returns the list of devices owned by the user.
    """
    device_repo = DeviceRepository(session)
    user_devices = await device_repo.get_devices_by_owner(current_user.id)
    
    return [
        {
            "id": str(d.id),
            "mac_address": d.mac_address,
            "loc": d.name or "Main feeder",
            "status": "Online" if d.is_online else "Offline",
            "is_active": d.is_active
        }
        for d in user_devices
    ]

