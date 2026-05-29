"""
app/core/exceptions.py
======================
Domain and application exception hierarchy.

Design:
- All custom exceptions inherit from AmpAwareBaseError.
- Each exception carries a machine-readable `error_code` string
  (useful for frontend i18n and monitoring alert rules).
- HTTP status codes are NOT embedded here — that mapping lives in
  app/api/v1/error_handlers.py.  Domain exceptions must remain
  HTTP-agnostic.
"""
from __future__ import annotations

from typing import Any


class AmpAwareBaseError(Exception):
    """Root of the exception hierarchy."""

    error_code: str = "INTERNAL_ERROR"
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, **context: Any) -> None:
        self.message = message or self.default_message
        self.context = context
        super().__init__(self.message)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code!r}, "
            f"message={self.message!r}, "
            f"context={self.context!r})"
        )


# ---------------------------------------------------------------------------
# Configuration errors (startup-time)
# ---------------------------------------------------------------------------


class ConfigurationError(AmpAwareBaseError):
    error_code = "CONFIGURATION_ERROR"
    default_message = "Invalid application configuration."


# ---------------------------------------------------------------------------
# Authentication & Authorization
# ---------------------------------------------------------------------------


class AuthenticationError(AmpAwareBaseError):
    error_code = "AUTHENTICATION_FAILED"
    default_message = "Authentication failed."


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"
    default_message = "Authentication token has expired."


class TokenInvalidError(AuthenticationError):
    error_code = "TOKEN_INVALID"
    default_message = "Authentication token is invalid."


class PermissionDeniedError(AmpAwareBaseError):
    error_code = "PERMISSION_DENIED"
    default_message = "You do not have permission to perform this action."


# ---------------------------------------------------------------------------
# Resource errors
# ---------------------------------------------------------------------------


class NotFoundError(AmpAwareBaseError):
    error_code = "NOT_FOUND"
    default_message = "The requested resource was not found."


class AlreadyExistsError(AmpAwareBaseError):
    error_code = "ALREADY_EXISTS"
    default_message = "A resource with this identifier already exists."


class ConflictError(AmpAwareBaseError):
    error_code = "CONFLICT"
    default_message = "The operation conflicts with the current state."


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class ValidationError(AmpAwareBaseError):
    error_code = "VALIDATION_FAILED"
    default_message = "Input validation failed."


class TelemetryValidationError(ValidationError):
    error_code = "TELEMETRY_VALIDATION_FAILED"
    default_message = "Telemetry payload failed validation."


class TimestampError(TelemetryValidationError):
    error_code = "TIMESTAMP_INVALID"
    default_message = "Telemetry timestamp is outside acceptable bounds."


class DuplicatePacketError(TelemetryValidationError):
    error_code = "DUPLICATE_PACKET"
    default_message = "Duplicate telemetry packet detected."


class OutOfOrderPacketError(TelemetryValidationError):
    error_code = "OUT_OF_ORDER_PACKET"
    default_message = "Telemetry packet arrived out of order."


# ---------------------------------------------------------------------------
# Device errors
# ---------------------------------------------------------------------------


class DeviceNotFoundError(NotFoundError):
    error_code = "DEVICE_NOT_FOUND"
    default_message = "Device was not found."


class DeviceAuthenticationError(AuthenticationError):
    error_code = "DEVICE_AUTHENTICATION_FAILED"
    default_message = "Device authentication failed."


class DeviceInactiveError(AmpAwareBaseError):
    error_code = "DEVICE_INACTIVE"
    default_message = "Device is not active."


# ---------------------------------------------------------------------------
# Calculation & energy engine errors
# ---------------------------------------------------------------------------


class CalculationError(AmpAwareBaseError):
    error_code = "CALCULATION_ERROR"
    default_message = "An error occurred during power calculation."


class EnergyAccumulationError(AmpAwareBaseError):
    error_code = "ENERGY_ACCUMULATION_ERROR"
    default_message = "An error occurred in the energy accumulation engine."


# ---------------------------------------------------------------------------
# Tariff & billing errors
# ---------------------------------------------------------------------------


class TariffNotFoundError(NotFoundError):
    error_code = "TARIFF_NOT_FOUND"
    default_message = "No applicable tariff was found for the given parameters."


class BillingError(AmpAwareBaseError):
    error_code = "BILLING_ERROR"
    default_message = "An error occurred during bill computation."


# ---------------------------------------------------------------------------
# Infrastructure errors
# ---------------------------------------------------------------------------


class DatabaseError(AmpAwareBaseError):
    error_code = "DATABASE_ERROR"
    default_message = "A database error occurred."


class RedisError(AmpAwareBaseError):
    error_code = "CACHE_ERROR"
    default_message = "A cache (Redis) error occurred."


class ExternalServiceError(AmpAwareBaseError):
    error_code = "EXTERNAL_SERVICE_ERROR"
    default_message = "An external service call failed."


class RateLimitExceededError(AmpAwareBaseError):
    error_code = "RATE_LIMIT_EXCEEDED"
    default_message = "Rate limit exceeded. Please slow down requests."
