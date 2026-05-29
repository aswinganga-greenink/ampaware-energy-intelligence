"""
app/api/v1/router.py
====================
Master API router that aggregates all v1 endpoints.

Each module registers its own APIRouter here.
Phases 3+ will add more endpoint modules as they are built.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard, health, telemetry

api_v1_router = APIRouter()

# --- Core system ---
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# --- Devices & Ingestion ---
api_v1_router.include_router(
    telemetry.router, prefix="/telemetry", tags=["telemetry"]
)
