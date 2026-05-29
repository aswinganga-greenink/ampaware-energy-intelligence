"""
app/utils/datetime_utils.py
============================
Timezone-aware datetime utilities.

All timestamps in AmpAware are stored in UTC internally.
Timezone conversion (e.g., to IST for display) happens only at the
API response layer, never inside business logic or DB models.

DST handling: Python's zoneinfo module (stdlib 3.9+) is used instead of
pytz. It correctly handles DST transitions and IANA time zone changes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
UTC = timezone.utc


def utcnow() -> datetime:
    """Return current time as UTC-aware datetime."""
    return datetime.now(UTC)


def to_utc(dt: datetime) -> datetime:
    """Convert any tz-aware datetime to UTC. Raises if dt is naive."""
    if dt.tzinfo is None:
        raise ValueError(
            f"Naive datetime passed to to_utc(): {dt!r}. "
            "All datetimes must be timezone-aware."
        )
    return dt.astimezone(UTC)


def to_ist(dt: datetime) -> datetime:
    """Convert UTC datetime to IST (Asia/Kolkata, UTC+5:30)."""
    return dt.astimezone(IST)


def from_unix_timestamp(ts: float) -> datetime:
    """Convert a Unix epoch (seconds) to UTC-aware datetime."""
    return datetime.fromtimestamp(ts, tz=UTC)


def to_unix_timestamp(dt: datetime) -> float:
    """Convert a UTC-aware datetime to Unix epoch seconds."""
    return dt.timestamp()


def delta_seconds(earlier: datetime, later: datetime) -> float:
    """
    Return signed elapsed seconds between two UTC-aware datetimes.

    Negative result means `earlier` is actually after `later`.
    """
    return (later - earlier).total_seconds()


def floor_to_hour(dt: datetime) -> datetime:
    """Truncate datetime to the start of the hour (UTC)."""
    return dt.replace(minute=0, second=0, microsecond=0)


def floor_to_day(dt: datetime) -> datetime:
    """Truncate datetime to UTC midnight."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def is_same_day_utc(a: datetime, b: datetime) -> bool:
    return floor_to_day(a) == floor_to_day(b)
