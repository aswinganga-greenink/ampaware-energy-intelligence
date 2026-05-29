"""
app/api/v1/endpoints/health.py
==============================
System health check endpoint.

Provides:
- GET /api/v1/health          — lightweight liveness probe (no I/O)
- GET /api/v1/health/detailed — readiness probe with all subsystem checks

The detailed probe is used by:
- Docker HEALTHCHECK
- Kubernetes readiness probes
- Load balancer health checks
- Monitoring dashboards

Never cache the detailed health response — it must reflect live state.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.infrastructure.redis.client import get_redis, ping_redis
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["health"])

_APP_START_TIME = time.time()


class ComponentHealth(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    app_name: str
    version: str
    environment: str
    uptime_seconds: float
    components: dict[str, ComponentHealth]


@router.get(
    "/health",
    summary="Liveness probe",
    description="Returns 200 OK immediately. Use for liveness checks only.",
    status_code=status.HTTP_200_OK,
)
async def liveness() -> dict[str, str]:
    """Minimal liveness check — no I/O, never fails."""
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@router.get(
    "/health/detailed",
    summary="Readiness probe (detailed)",
    description=(
        "Checks all subsystem connectivity. "
        "Returns 200 if all critical components are healthy, "
        "503 if any critical component is down."
    ),
    response_model=HealthResponse,
)
async def readiness(
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """Detailed readiness check. Probes DB and Redis."""
    settings = get_settings()
    components: dict[str, ComponentHealth] = {}
    overall_ok = True

    # --- PostgreSQL ---
    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - t0) * 1000
        components["postgresql"] = ComponentHealth(
            status="ok", latency_ms=round(db_latency, 2)
        )
    except Exception as exc:
        components["postgresql"] = ComponentHealth(
            status="error", detail=str(exc)
        )
        overall_ok = False
        logger.error("health.db.failed", error=str(exc))

    # --- Redis ---
    t0 = time.perf_counter()
    try:
        ok = await ping_redis()
        redis_latency = (time.perf_counter() - t0) * 1000
        components["redis"] = ComponentHealth(
            status="ok" if ok else "error",
            latency_ms=round(redis_latency, 2),
        )
        if not ok:
            overall_ok = False
    except Exception as exc:
        components["redis"] = ComponentHealth(
            status="error", detail=str(exc)
        )
        overall_ok = False
        logger.error("health.redis.failed", error=str(exc))

    response_status = "ok" if overall_ok else "error"
    http_code = (
        status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    body = HealthResponse(
        status=response_status,
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _APP_START_TIME, 1),
        components=components,
    )
    return JSONResponse(status_code=http_code, content=body.model_dump())
