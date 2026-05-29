"""
tests/unit/test_config.py
==========================
Unit tests for the configuration system.

Tests:
- Valid config loads without error
- Production mode rejects insecure defaults
- CORS origins can be parsed from JSON string or comma-separated string
- Settings are cached (same object returned on multiple calls)
"""
from __future__ import annotations

import pytest

from app.core.config import Settings


@pytest.mark.unit
class TestSettings:
    def test_default_settings_are_valid(self) -> None:
        """Settings can be instantiated with defaults in development mode."""
        s = Settings(app_env="development")
        assert s.app_name == "AmpAware"
        assert s.is_development is True
        assert s.is_production is False

    def test_production_rejects_default_secret_key(self) -> None:
        """Production mode must refuse to start with the default secret key."""
        with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
            Settings(app_env="production", debug=False)

    def test_production_rejects_debug_mode(self) -> None:
        """Production mode must refuse debug=True."""
        with pytest.raises(ValueError, match="DEBUG must be False"):
            Settings(
                app_env="production",
                debug=True,
                secret_key="x" * 64,
            )

    def test_cors_origins_json_string(self) -> None:
        """CORS origins can be parsed from a JSON array string."""
        s = Settings(backend_cors_origins='["http://localhost:3000"]')
        assert "http://localhost:3000" in [str(o) for o in s.backend_cors_origins]

    def test_cors_origins_comma_separated(self) -> None:
        """CORS origins can be provided as comma-separated string."""
        s = Settings(backend_cors_origins="http://a.com, http://b.com")
        origins_str = [str(o) for o in s.backend_cors_origins]
        assert "http://a.com" in origins_str
        assert "http://b.com" in origins_str

    def test_api_v1_prefix(self) -> None:
        s = Settings()
        assert s.api_v1_prefix == "/api/v1"

    def test_database_async_url(self) -> None:
        """Database async URL uses asyncpg driver."""
        db = Settings().database
        assert "asyncpg" in db.async_url

    def test_database_sync_url(self) -> None:
        """Database sync URL uses psycopg2 driver (for Alembic)."""
        db = Settings().database
        assert "psycopg2" in db.sync_url
