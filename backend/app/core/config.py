"""
app/core/config.py
==================
Central application configuration using Pydantic Settings v2.

All settings are read from environment variables (or .env file).
Strict validation ensures the application refuses to start with
invalid or missing configuration — fail-fast at startup, not at runtime.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection & pool settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="POSTGRES_",
        populate_by_name=True,
        extra="ignore",
    )

    host: str = Field(default="localhost")
    port: int = Field(default=5432, ge=1, le=65535)
    db: str = Field(default="ampaware")
    user: str = Field(default="ampaware_user")
    password: str = Field(default="change-me")

    pool_size: int = Field(default=10, ge=1, le=100, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, ge=0, le=200, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, ge=1, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=1800, ge=60, alias="DB_POOL_RECYCLE")
    echo_sql: bool = Field(default=False, alias="DB_ECHO_SQL")

    # (removed duplicated model_config below)

    @property
    def async_url(self) -> str:
        """Async SQLAlchemy DSN using asyncpg driver."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )

    @property
    def sync_url(self) -> str:
        """Sync SQLAlchemy DSN used only by Alembic migrations."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0, le=15)
    password: str | None = Field(default=None)
    max_connections: int = Field(default=50, ge=1)
    socket_timeout: float = Field(default=5.0, gt=0)
    connect_timeout: float = Field(default=5.0, gt=0)

    @property
    def url(self) -> str:
        """Redis URL with optional auth."""
        auth = f":{self.password}@" if self.password and self.password.strip() else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class JWTSettings(BaseSettings):
    """JWT token configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="JWT_",
        extra="ignore",
    )

    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60, ge=1)
    refresh_token_expire_days: int = Field(default=30, ge=1)


class TelemetryIngestionSettings(BaseSettings):
    """Controls on telemetry acceptance."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TELEMETRY_",
        extra="ignore",
    )

    max_future_seconds: int = Field(
        default=60,
        ge=0,
        description="Reject readings timestamped more than N seconds in the future.",
    )
    max_past_seconds: int = Field(
        default=86400,
        ge=60,
        description="Reject readings timestamped more than N seconds in the past.",
    )
    dedup_window_seconds: int = Field(
        default=5,
        ge=1,
        description="Deduplicate identical device packets within this window.",
    )


class LoggingSettings(BaseSettings):
    """Structured logging configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LOG_",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    format: Literal["json", "pretty"] = Field(default="json")
    file_path: Path | None = Field(default=Path("logs/ampaware.log"))
    rotation_bytes: int = Field(default=10 * 1024 * 1024)
    backup_count: int = Field(default=5, ge=1)


class RateLimitSettings(BaseSettings):
    """Rate limiting knobs."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="RATE_LIMIT_",
        extra="ignore",
    )

    enabled: bool = Field(default=True)
    default_per_minute: int = Field(default=120, ge=1)
    telemetry_per_minute: int = Field(default=600, ge=1)


class OtelSettings(BaseSettings):
    """OpenTelemetry tracing configuration (opt-in)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OTEL_",
        extra="ignore",
    )

    enabled: bool = Field(default=False)
    service_name: str = Field(default="ampaware-backend")
    exporter_otlp_endpoint: str = Field(default="http://localhost:4317")


class Settings(BaseSettings):
    """
    Root application settings.

    Aggregates all subsystem configs.  A single call to get_settings()
    returns a fully-validated, cached instance usable across the app.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    # --- Core ---
    app_name: str = Field(default="AmpAware")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-me-to-a-64-char-random-secret")

    # --- Seed / Admin ---
    admin_email: str = Field(default="admin@ampaware.com")
    admin_password: str = Field(default="password123")

    # --- API ---
    api_v1_prefix: str = Field(default="/api/v1")
    backend_cors_origins: list[AnyHttpUrl] | list[str] = Field(default=["*"])

    # --- Pagination ---
    default_page_size: int = Field(default=50, ge=1)
    max_page_size: int = Field(default=500, ge=1)

    # --- Scheduler ---
    scheduler_timezone: str = Field(default="Asia/Kolkata")
    scheduler_coalesce: bool = Field(default=True)
    scheduler_max_instances: int = Field(default=3, ge=1)

    # --- Subsystem configs (loaded separately via env prefix) ---
    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings()

    @property
    def redis(self) -> RedisSettings:
        return RedisSettings()

    @property
    def jwt(self) -> JWTSettings:
        return JWTSettings()

    @property
    def telemetry_ingestion(self) -> TelemetryIngestionSettings:
        return TelemetryIngestionSettings()

    @property
    def logging(self) -> LoggingSettings:
        return LoggingSettings()

    @property
    def rate_limit(self) -> RateLimitSettings:
        return RateLimitSettings()

    @property
    def otel(self) -> OtelSettings:
        return OtelSettings()

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> list[str]:
        """Accept JSON array string or comma-separated string from env."""
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforce stricter checks in production to prevent insecure deployments."""
        if self.app_env == "production":
            if self.secret_key.startswith("change-me"):
                raise ValueError(
                    "SECRET_KEY must be changed from the default value in production."
                )
            if self.debug:
                raise ValueError("DEBUG must be False in production.")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.

    Using lru_cache ensures we parse the environment only once per process,
    which is important for performance and for predictable behavior in tests
    (tests can clear the cache to inject different settings).
    """
    return Settings()
