"""
app/domain/schemas/telemetry.py
===============================
Pydantic schemas for telemetry data transfer.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryIngestPayload(BaseModel):
    """
    Schema for raw telemetry payloads pushed by the smart meters.
    """

    sequence_number: int = Field(..., description="Device monotonic sequence counter")
    recorded_at: datetime = Field(
        ..., description="Timestamp of recording from device RTC (UTC)"
    )

    voltage_v: float = Field(..., description="RMS Voltage (V)")
    current_a: float = Field(..., description="RMS Current (A)", ge=0)
    active_power_w: float = Field(..., description="Active Power (W)")
    reactive_power_var: float = Field(..., description="Reactive Power (VAR)")
    apparent_power_va: float = Field(..., description="Apparent Power (VA)", ge=0)
    power_factor: float = Field(..., description="Power Factor", ge=0, le=1.0)
    frequency_hz: float = Field(..., description="Grid Frequency (Hz)", ge=40, le=70)
