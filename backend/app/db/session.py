"""
app/db/session.py
=================
Async SQLAlchemy engine and session factory.

Design decisions:
- Uses SQLAlchemy 2.0 async API exclusively (no legacy 1.x patterns).
- NullPool is used during Alembic migrations (sync context); AsyncAdaptedQueuePool
  is used at runtime for proper connection pooling.
- The async_session_factory is a context-manager-friendly sessionmaker that
  yields AsyncSession objects with autocommit=False and autoflush=False.
  This gives service/repository layers full control over transaction boundaries.
- Engine is created once per process and shared (thread-safe via pool).
- pool_pre_ping=True detects stale connections transparently.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    """Construct the async SQLAlchemy engine from settings."""
    settings = get_settings()
    db = settings.database

    connect_args: dict[str, Any] = {
        # asyncpg-specific: server-side statement timeout (ms)
        "server_settings": {
            "application_name": settings.app_name,
            "jit": "off",  # JIT adds latency for short OLTP queries
        },
    }

    engine = create_async_engine(
        db.async_url,
        pool_size=db.pool_size,
        max_overflow=db.max_overflow,
        pool_timeout=db.pool_timeout,
        pool_recycle=db.pool_recycle,
        pool_pre_ping=True,   # detect dead connections before checkout
        echo=db.echo_sql,
        connect_args=connect_args,
        future=True,
    )
    logger.info(
        "db.engine.created",
        host=db.host,
        port=db.port,
        database=db.db,
        pool_size=db.pool_size,
        max_overflow=db.max_overflow,
    )
    return engine


def get_engine() -> AsyncEngine:
    """Return the process-level async engine (created lazily)."""
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-level async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a scoped AsyncSession.

    Transaction lifecycle:
    - A new session is opened per request.
    - The caller (service layer) is responsible for commit/rollback.
    - If an unhandled exception propagates, the session is rolled back
      automatically before being closed.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    factory = get_async_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    """
    Gracefully dispose the connection pool.

    Must be called during application shutdown to allow all pooled
    connections to be properly closed before the process exits.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("db.engine.disposed")
        _engine = None
