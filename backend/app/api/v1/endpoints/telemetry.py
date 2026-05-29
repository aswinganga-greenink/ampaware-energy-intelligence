"""
app/api/v1/endpoints/telemetry.py
=================================
IoT telemetry ingestion endpoints.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import (
    get_anomaly_service,
    get_device_token,
    get_energy_service,
    get_telemetry_service,
)
from app.domain.models.device import Device
from app.domain.schemas.telemetry import TelemetryIngestPayload
from app.services.anomaly import AnomalyService
from app.services.energy import EnergyAggregationService
from app.services.telemetry import TelemetryService

router = APIRouter(tags=["telemetry"])


@router.post(
    "/ingest",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest Smart Meter Telemetry",
)
async def ingest_telemetry(
    request: Request,
    payload: TelemetryIngestPayload,
    device: Device = Depends(get_device_token),
    telemetry_svc: TelemetryService = Depends(get_telemetry_service),
    anomaly_svc: AnomalyService = Depends(get_anomaly_service),
    energy_svc: EnergyAggregationService = Depends(get_energy_service),
) -> dict[str, str]:
    """
    Ingest a raw telemetry payload from an authenticated smart meter.
    
    Steps:
    1. Authenticate hardware token (via Depends).
    2. Persist telemetry and check for duplicates (Redis).
    3. Evaluate real-time electrical anomalies (Voltage, PF).
    4. Compute energy (Wh) delta and update aggregates idempotently.
    """
    raw_payload = await request.json()
    
    # 1 & 2. Deduplication and Ingestion
    reading = await telemetry_svc.ingest_payload(
        device_id=device.id,
        payload=payload,
        raw_payload_json=raw_payload,
    )

    # 3. Anomaly Evaluation
    if reading.is_valid:
        await anomaly_svc.evaluate_telemetry_for_anomalies(reading)

        # 4. Energy Aggregation
        await energy_svc.process_telemetry_to_energy(reading)

    return {"status": "accepted", "sequence": str(payload.sequence_number)}
