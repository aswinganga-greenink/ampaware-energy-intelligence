"""
app/api/v1/error_handlers.py
============================
Global exception → HTTP response mapping.

Design:
- Maps domain exceptions to specific HTTP status codes.
- Preserves machine-readable error_code in the response body.
- Never exposes stack traces in production responses.
- Returns a consistent JSON envelope for all error responses:

  {
    "error_code": "DEVICE_NOT_FOUND",
    "message": "Device was not found.",
    "details": {}         // optional, only in debug mode
  }
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import get_settings
from app.core.exceptions import (
    AlreadyExistsError,
    AmpAwareBaseError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitExceededError,
    ValidationError as AppValidationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
) -> JSONResponse:
    body: dict = {"error_code": error_code, "message": message}
    if details and get_settings().debug:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app."""

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_404_NOT_FOUND)

    @app.exception_handler(AuthenticationError)
    async def handle_auth(request: Request, exc: AuthenticationError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(PermissionDeniedError)
    async def handle_forbidden(
        request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_403_FORBIDDEN)

    @app.exception_handler(AlreadyExistsError)
    async def handle_conflict_exists(
        request: Request, exc: AlreadyExistsError
    ) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_409_CONFLICT)

    @app.exception_handler(ConflictError)
    async def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return _error_response(exc.error_code, exc.message, status.HTTP_409_CONFLICT)

    @app.exception_handler(AppValidationError)
    async def handle_validation(
        request: Request, exc: AppValidationError
    ) -> JSONResponse:
        from app.core.exceptions import DuplicatePacketError
        
        if isinstance(exc, DuplicatePacketError):
            return _error_response(
                exc.error_code, exc.message, status.HTTP_409_CONFLICT
            )
            
        return _error_response(
            exc.error_code, exc.message, status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    @app.exception_handler(RateLimitExceededError)
    async def handle_rate_limit(
        request: Request, exc: RateLimitExceededError
    ) -> JSONResponse:
        return _error_response(
            exc.error_code, exc.message, status.HTTP_429_TOO_MANY_REQUESTS
        )

    @app.exception_handler(AmpAwareBaseError)
    async def handle_app_error(
        request: Request, exc: AmpAwareBaseError
    ) -> JSONResponse:
        logger.error(
            "unhandled.app.exception",
            error_code=exc.error_code,
            message=exc.message,
            context=exc.context,
            path=str(request.url),
        )
        return _error_response(
            exc.error_code, exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @app.exception_handler(PydanticValidationError)
    async def handle_pydantic_validation(
        request: Request, exc: PydanticValidationError
    ) -> JSONResponse:
        return _error_response(
            "VALIDATION_FAILED",
            "Request body validation failed.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled.exception",
            exc_type=type(exc).__name__,
            path=str(request.url),
        )
        return _error_response(
            "INTERNAL_ERROR",
            "An unexpected internal error occurred.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
