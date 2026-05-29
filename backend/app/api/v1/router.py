"""
app/api/v1/router.py
====================
Master API router that aggregates all v1 endpoints.

Each module registers its own APIRouter here.
Phases 3+ will add more endpoint modules as they are built.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_v1_router = APIRouter()

# --- Core system ---
api_v1_router.include_router(health.router)

# Future phases will add:
# from app.api.v1.endpoints import devices, telemetry, billing, analytics, ...
# api_v1_router.include_router(devices.router, prefix="/devices", tags=["devices"])
