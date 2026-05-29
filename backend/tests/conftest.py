"""
tests/conftest.py
=================
Pytest configuration and shared fixtures.

Fixtures:
- settings          — test Settings with overrides (no real secrets)
- async_client      — AsyncClient pointing at the test app
- db_session        — in-memory async SQLite session (unit tests)
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import create_application


import os

if "REDIS_PASSWORD" in os.environ:
    del os.environ["REDIS_PASSWORD"]

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Return settings safe for testing (no production secrets)."""
    return Settings(
        app_env="development",
        debug=True,
        secret_key="test-secret-key-exactly-64-chars-long-padding-padding-padding",
    )


@pytest.fixture(scope="session")
def app(test_settings):
    """Create a FastAPI test application."""
    # Override the settings singleton for the test session
    get_settings.cache_clear()
    application = create_application()
    return application


@pytest_asyncio.fixture
async def async_client(app) -> AsyncClient:
    """Async HTTP client for integration tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    """Real async PostgreSQL session for integration tests."""
    from app.db.session import get_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker

    engine = get_engine()
    TestingSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )

    async with TestingSessionLocal() as session:
        yield session
        # Rollback all integration test changes
        await session.rollback()
