"""
tests/unit/test_datetime_utils.py
==================================
Unit tests for datetime utility functions.

All tests are pure in-memory, no I/O.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.utils.datetime_utils import (
    IST,
    UTC,
    delta_seconds,
    floor_to_day,
    floor_to_hour,
    from_unix_timestamp,
    is_same_day_utc,
    to_ist,
    to_unix_timestamp,
    to_utc,
    utcnow,
)


@pytest.mark.unit
class TestDatetimeUtils:
    def test_utcnow_is_aware(self) -> None:
        now = utcnow()
        assert now.tzinfo is not None
        assert now.utcoffset().total_seconds() == 0

    def test_to_utc_converts_ist_to_utc(self) -> None:
        # IST is UTC+5:30, so 12:00 IST = 06:30 UTC
        ist_noon = datetime(2024, 7, 1, 12, 0, 0, tzinfo=IST)
        utc_time = to_utc(ist_noon)
        assert utc_time.hour == 6
        assert utc_time.minute == 30
        assert utc_time.tzinfo == UTC

    def test_to_utc_raises_on_naive_datetime(self) -> None:
        with pytest.raises(ValueError, match="Naive datetime"):
            to_utc(datetime(2024, 1, 1, 12, 0, 0))

    def test_to_ist_converts_utc_to_ist(self) -> None:
        utc_time = datetime(2024, 7, 1, 6, 30, 0, tzinfo=UTC)
        ist_time = to_ist(utc_time)
        assert ist_time.hour == 12
        assert ist_time.minute == 0

    def test_from_unix_timestamp(self) -> None:
        ts = 1_000_000_000.0  # 2001-09-09T01:46:40Z
        dt = from_unix_timestamp(ts)
        assert dt.tzinfo == UTC
        assert dt.year == 2001

    def test_to_unix_timestamp_roundtrip(self) -> None:
        original = 1_700_000_000.0
        dt = from_unix_timestamp(original)
        assert abs(to_unix_timestamp(dt) - original) < 0.001

    def test_delta_seconds_positive(self) -> None:
        earlier = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        later = datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC)
        assert delta_seconds(earlier, later) == pytest.approx(60.0)

    def test_delta_seconds_negative(self) -> None:
        earlier = datetime(2024, 1, 1, 0, 1, 0, tzinfo=UTC)
        later = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert delta_seconds(earlier, later) == pytest.approx(-60.0)

    def test_floor_to_hour(self) -> None:
        dt = datetime(2024, 7, 1, 14, 37, 52, tzinfo=UTC)
        floored = floor_to_hour(dt)
        assert floored.minute == 0
        assert floored.second == 0
        assert floored.hour == 14

    def test_floor_to_day(self) -> None:
        dt = datetime(2024, 7, 1, 22, 45, 0, tzinfo=UTC)
        floored = floor_to_day(dt)
        assert floored.hour == 0
        assert floored.minute == 0
        assert floored.day == 1

    def test_is_same_day_utc_true(self) -> None:
        a = datetime(2024, 7, 1, 0, 0, 0, tzinfo=UTC)
        b = datetime(2024, 7, 1, 23, 59, 59, tzinfo=UTC)
        assert is_same_day_utc(a, b) is True

    def test_is_same_day_utc_false(self) -> None:
        a = datetime(2024, 7, 1, 23, 59, 59, tzinfo=UTC)
        b = datetime(2024, 7, 2, 0, 0, 0, tzinfo=UTC)
        assert is_same_day_utc(a, b) is False
