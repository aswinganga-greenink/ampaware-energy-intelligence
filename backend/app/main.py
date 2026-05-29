"""
app/main.py
===========
FastAPI application factory.

Uses the lifespan context manager (FastAPI 0.93+) instead of the deprecated
on_event decorators — lifespan provides cleaner startup/shutdown sequencing
and works correctly with pytest-asyncio fixtures.

Application startup sequence:
1. Configure structured logging
2. Validate settings (Pydantic raises immediately if config is invalid)
3. Create DB engine (lazy; first actual query triggers pool creation)
4. Ping Redis to confirm connectivity
5. Mount middleware (CORS, correlation ID, request logging, security headers)
6. Register exception handlers
7. Register routers

Shutdown sequence:
1. Dispose DB connection pool (allows in-flight queries to finish)
2. Close Redis connection pool
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.error_handlers import register_exception_handlers
from app.api.v1.middleware import (
    CorrelationIDMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import dispose_engine, get_engine
from app.infrastructure.redis.client import close_redis, ping_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager (startup → yield → shutdown)."""
    # --- Startup ---
    configure_logging()
    logger = get_logger(__name__)
    settings = get_settings()

    logger.info(
        "app.startup",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )

    # Eagerly create the DB engine so pool warming happens at boot
    get_engine()

    # Verify Redis connectivity at startup
    if not await ping_redis():
        logger.warning("startup.redis.unreachable")
    else:
        logger.info("startup.redis.connected")

    yield  # ← application runs here

    # --- Shutdown ---
    logger.info("app.shutdown.started")
    await dispose_engine()
    await close_redis()
    logger.info("app.shutdown.complete")


def create_application() -> FastAPI:
    """
    Factory function that constructs and configures the FastAPI application.

    Separation from module-level instantiation allows:
    - Pytest to create isolated app instances per test suite
    - Multiple app variants (e.g., admin-only app) from the same factory
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AmpAware — Industrial-grade smart energy metering backend. "
            "Receives telemetry from ESP32 smart meters and provides "
            "real-time power analytics, KSEB billing estimation, and "
            "anomaly detection for homes, schools, offices, and factories."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Custom middleware (applied in reverse registration order) ---
    # Last registered = outermost (first to run on request)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routers ---
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


# Module-level app instance consumed by uvicorn
app = create_application()
