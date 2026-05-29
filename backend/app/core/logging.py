"""
app/core/logging.py
===================
Structured, production-grade logging setup.

Design decisions:
- Uses `structlog` for structured (JSON) logging with contextual bindings.
- Falls back to Python's standard logging in development with colorized output.
- Each log record includes: timestamp (ISO-8601), level, logger name,
  correlation request_id (set per-request), and any extra fields.
- Log rotation is handled at the handler level (not at the process level)
  so multi-worker deployments can each write their own rotated files.
- OpenTelemetry trace/span IDs are injected when OTEL is enabled.

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("device.registered", device_id=str(device.id), serial=device.serial)
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import LoggingSettings, get_settings


# ---------------------------------------------------------------------------
# Custom structlog processors
# ---------------------------------------------------------------------------


def _add_log_level(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add stdlib-compatible 'level' key."""
    event_dict.setdefault("level", method_name.upper())
    return event_dict


def _drop_color_message_key(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Remove the 'color_message' key injected by uvicorn's access logger."""
    event_dict.pop("color_message", None)
    return event_dict


def _add_otel_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Inject OpenTelemetry trace/span IDs when a span is active."""
    try:
        from opentelemetry import trace  # type: ignore[import]

        span = trace.get_current_span()
        if span and span.is_recording():
            ctx = span.get_span_context()
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except ImportError:
        pass
    return event_dict


# ---------------------------------------------------------------------------
# Setup function
# ---------------------------------------------------------------------------


def configure_logging() -> None:
    """
    Configure structlog + standard library logging.

    Must be called once at application startup (in lifespan or main.py).
    Idempotent — safe to call multiple times in tests.
    """
    settings = get_settings()
    log_cfg: LoggingSettings = settings.logging

    # Shared processors regardless of formatter
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_log_level,
        _drop_color_message_key,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        _add_otel_context,
    ]

    if log_cfg.format == "json":
        # Production: machine-parseable JSON
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=processors,
            foreign_pre_chain=shared_processors,
        )
    else:
        # Development: colorized human-readable output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=processors,
            foreign_pre_chain=shared_processors,
        )

    # --- Root handler: stderr ---
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [stream_handler]

    # --- Optional rotating file handler ---
    if log_cfg.file_path:
        log_cfg.file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_cfg.file_path,
            maxBytes=log_cfg.rotation_bytes,
            backupCount=log_cfg.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # --- Configure root logger ---
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for h in handlers:
        root_logger.addHandler(h)
    root_logger.setLevel(log_cfg.level)

    # --- Suppress noisy third-party loggers ---
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if settings.database.echo_sql:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    # --- Configure structlog ---
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_cfg.level)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Return a structlog bound logger for the given module name.

    Example:
        logger = get_logger(__name__)
        logger.info("event.name", key="value")
    """
    return structlog.get_logger(name)
