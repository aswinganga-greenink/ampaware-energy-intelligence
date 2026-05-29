"""
app/infrastructure/redis/client.py
===================================
Redis client factory and dependency.

Design:
- Uses redis-py's async client (redis.asyncio).
- A single connection pool is created per process and shared.
- All Redis keys are namespaced under "ampaware:" to avoid collisions
  with other services running on the same Redis instance.
- If Redis is unavailable, the application continues to function in
  degraded mode for non-critical paths (rate limiting, caching).
  Safety-critical paths (deduplication, distributed locks) must handle
  the RedisError exception explicitly.
"""
from __future__ import annotations

from typing import AsyncGenerator

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_pool: ConnectionPool | None = None
_client: Redis | None = None  # type: ignore[type-arg]

REDIS_NAMESPACE = "ampaware"


def _make_pool() -> ConnectionPool:
    """Build the Redis connection pool from settings."""
    cfg = get_settings().redis
    pool = aioredis.ConnectionPool.from_url(
        cfg.url,
        max_connections=cfg.max_connections,
        socket_timeout=cfg.socket_timeout,
        socket_connect_timeout=cfg.connect_timeout,
        decode_responses=True,
        encoding="utf-8",
        health_check_interval=30,  # background ping every 30s
    )
    logger.info(
        "redis.pool.created",
        host=cfg.host,
        port=cfg.port,
        db=cfg.db,
        max_connections=cfg.max_connections,
    )
    return pool


def get_redis_pool() -> ConnectionPool:
    """Return the process-level connection pool (lazy init)."""
    global _pool
    if _pool is None:
        _pool = _make_pool()
    return _pool


def get_redis_client() -> Redis:  # type: ignore[type-arg]
    """Return a Redis client backed by the shared pool."""
    global _client
    if _client is None:
        _client = aioredis.Redis(connection_pool=get_redis_pool())
    return _client


async def get_redis() -> AsyncGenerator[Redis, None]:  # type: ignore[type-arg]
    """
    FastAPI dependency that yields the shared Redis client.

    Usage:
        @router.get("/")
        async def endpoint(redis: Redis = Depends(get_redis)):
            ...
    """
    yield get_redis_client()


async def close_redis() -> None:
    """Gracefully close the Redis pool on application shutdown."""
    global _pool, _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
        logger.info("redis.pool.closed")


def redis_key(*parts: str) -> str:
    """
    Build a namespaced Redis key.

    Example:
        redis_key("device", device_id, "last_seen")
        → "ampaware:device:<uuid>:last_seen"
    """
    return ":".join([REDIS_NAMESPACE, *parts])


async def ping_redis() -> bool:
    """
    Return True if Redis responds to PING.
    Used by the health check endpoint.
    """
    try:
        client = get_redis_client()
        return await client.ping()
    except Exception as exc:
        logger.warning("redis.ping.failed", error=str(exc))
        return False
