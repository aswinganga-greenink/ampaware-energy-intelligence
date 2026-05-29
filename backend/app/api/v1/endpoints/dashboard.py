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
        
        # Get today's total kwh
        from app.db.repositories.energy import EnergyAggregateRepository
        from datetime import datetime, timezone
        from app.utils.datetime_utils import to_ist
        agg_repo = EnergyAggregateRepository(session)
        now_ist = to_ist(datetime.utcnow())
        daily_agg = await agg_repo.get_daily_aggregate(device_ids[0], now_ist.date())
        today_kwh = (float(daily_agg.total_active_energy_wh) / 1000) if daily_agg else 0.0

        if latest_reading:
            live_metrics = {
                "v": float(latest_reading.phase_a_voltage or 0),
                "a": float(latest_reading.phase_a_current or 0),
                "w": int(latest_reading.total_active_power_w or 0),
                "pf": float(latest_reading.total_power_factor or 0),
                "kwh": round(today_kwh, 2),
                "devices": total_active_devices
            }
    
        # Get weekly data
        from datetime import timedelta
        week_data = []
        for i in range(6, -1, -1):
            target_date = now_ist.date() - timedelta(days=i)
            d_agg = await agg_repo.get_daily_aggregate(device_ids[0], target_date)
            week_data.append({
                "d": target_date.strftime("%a"),
                "kwh": (float(d_agg.total_active_energy_wh) / 1000) if d_agg else 0.0
            })
            
        # Get daily (hourly) load curve
        day_data = []
        from zoneinfo import ZoneInfo
        IST = ZoneInfo("Asia/Kolkata")
        for h in range(24):
            # Create IST aware datetime for that hour, then convert to UTC
            hour_ist = datetime(now_ist.year, now_ist.month, now_ist.day, h, 0, 0, tzinfo=IST)
            hour_utc = hour_ist.astimezone(timezone.utc)
            h_agg = await agg_repo.get_hourly_aggregate(device_ids[0], hour_utc)
            # Power is Energy (Wh) * (3600/3600) -> Average Watts for the hour
            avg_w = float(h_agg.total_active_energy_wh) if h_agg else 0.0
            day_data.append({
                "h": f"{h:02d}:00",
                "load": round(avg_w)
            })
            
        # Device Breakdown (Live from actual devices)
        device_data = []
        if today_kwh > 0:
            for d in user_devices:
                d_agg = await agg_repo.get_daily_aggregate(d.id, now_ist.date())
                d_kwh = (float(d_agg.total_active_energy_wh) / 1000) if d_agg else 0.0
                if d_kwh > 0:
                    pct = round((d_kwh / today_kwh) * 100)
                    device_data.append({"name": d.name or "Main Feeder", "value": pct})
            
            # Ensure percentages sum to 100 exactly if there are any devices
            if device_data:
                total_pct = sum(item["value"] for item in device_data)
                if total_pct > 0 and total_pct != 100:
                    device_data[0]["value"] += (100 - total_pct)
        else:
            for d in user_devices:
                device_data.append({"name": d.name or "Main Feeder", "value": 0})
        
    return {
        "metrics": {
            "total_devices": len(device_ids),
            "active_devices": total_active_devices,
            "live": live_metrics,
            "week_data": week_data if device_ids else [],
            "day_data": day_data if device_ids else [],
            "device_data": device_data if device_ids else []
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
    from app.db.repositories.energy import EnergyAggregateRepository
    from datetime import datetime
    from app.utils.datetime_utils import to_ist
    import calendar

    # 1. Fetch user's devices
    device_repo = DeviceRepository(session)
    user_devices = await device_repo.get_devices_by_owner(current_user.id)
    device_ids = [d.id for d in user_devices]
    
    total_kwh = 0.0
    slabs_breakdown = []
    subtotal = 0.0
    duty = 0.0
    fixed_charge = 65.0
    total = 0.0
    cycle_days = []
    
    if device_ids:
        agg_repo = EnergyAggregateRepository(session)
        
        # Get monthly aggregate for billing
        now_ist = to_ist(datetime.utcnow())
        year, month = now_ist.year, now_ist.month
        
        # In a real app we'd sum across all devices, but let's just use the first for simplicity
        monthly_agg = await agg_repo.get_monthly_aggregate(device_ids[0], year, month)
        
        if monthly_agg:
            total_kwh = float(monthly_agg.total_active_energy_wh or 0) / 1000
            
            # Fetch daily aggregates to build chart data
            from calendar import monthrange
            days_in_month = monthrange(year, month)[1]
            
            # Populate cycle_days with actuals
            for i in range(1, days_in_month + 1):
                day_date = datetime(year, month, i).date()
                daily_agg = await agg_repo.get_daily_aggregate(device_ids[0], day_date)
                actual = (float(daily_agg.total_active_energy_wh) / 1000) if daily_agg else 0.0 if i <= now_ist.day else None
                forecast = (total_kwh / now_ist.day) * i if now_ist.day > 0 else 0
                
                cycle_days.append({
                    "d": i,
                    "actual": round(actual, 1) if actual is not None else None,
                    "forecast": round(forecast, 1)
                })

    # KSEB LT-1A Tariff Logic (Monthly)
    # If <= 250 units, use Telescopic slabs. If > 250 units, use Non-Telescopic (flat rate for all units).
    
    slabs_breakdown = []
    subtotal = 0.0
    
    # KSEB typically bills bi-monthly, but for this monthly dashboard we use the monthly equivalent slabs.
    if total_kwh <= 250:
        # Telescopic Slabs (2023-2024 rates)
        t_slabs = [
            {"range": "0–50", "rate": 3.25, "limit": 50},
            {"range": "51–100", "rate": 4.05, "limit": 50},
            {"range": "101–150", "rate": 5.10, "limit": 50},
            {"range": "151–200", "rate": 6.95, "limit": 50},
            {"range": "201–250", "rate": 8.20, "limit": 50},
        ]
        
        remaining_kwh = total_kwh
        for slab in t_slabs:
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
    else:
        # Non-Telescopic Slabs (Flat rate applies to ALL units)
        flat_rate = 0.0
        range_label = ""
        
        if total_kwh <= 300:
            flat_rate, range_label = 6.20, "0-300 (Non-Telescopic)"
        elif total_kwh <= 350:
            flat_rate, range_label = 7.00, "0-350 (Non-Telescopic)"
        elif total_kwh <= 400:
            flat_rate, range_label = 7.35, "0-400 (Non-Telescopic)"
        elif total_kwh <= 500:
            flat_rate, range_label = 7.60, "0-500 (Non-Telescopic)"
        else:
            flat_rate, range_label = 8.50, "Above 500 (Non-Telescopic)"
            
        subtotal = total_kwh * flat_rate
        slabs_breakdown.append({
            "range": range_label,
            "rate": f"₹{flat_rate:.2f} (Flat)",
            "units": round(total_kwh, 1),
            "amount": round(subtotal, 2)
        })
        
    duty = subtotal * 0.10  # 10% Electricity Duty
    total = subtotal + duty + fixed_charge
    
    return {
        "consumed_kwh": round(total_kwh, 2),
        "cycle_days": now_ist.day,
        "avg_per_day": round(total_kwh / max(now_ist.day, 1), 1),
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

