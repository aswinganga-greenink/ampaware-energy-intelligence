"""
app/api/v1/middleware.py
========================
Request/Response middleware stack.

Middleware chain (outer → inner):
1. CorrelationIDMiddleware  — injects X-Request-ID into structlog context
2. RequestLoggingMiddleware — logs method, path, status, duration
3. SecurityHeadersMiddleware — adds security HTTP headers

Middleware runs on every request before routing.
"""
from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Assign a unique request ID to every inbound request.

    Reads X-Request-ID from the incoming header if present (allows
    client-side tracing correlation); otherwise generates a new UUID4.
    The ID is:
    - Stored in structlog context (available to all log lines for this request)
    - Echoed back in the X-Request-ID response header
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured access log for every HTTP request/response.

    Logs:
    - HTTP method and path
    - Response status code
    - Duration in milliseconds
    - Client IP (respects X-Forwarded-For for proxy deployments)
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query),
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            client_ip=client_ip,
        )
        response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security-hardening HTTP response headers.

    These do not replace a proper WAF/API gateway but are cheap
    baseline protections for direct deployments.
    """

    _HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    }

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        for header, value in self._HEADERS.items():
            response.headers[header] = value
        return response
