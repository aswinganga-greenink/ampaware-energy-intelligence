"""
app/domain/enums/time_of_day.py
================================
Time-of-day (TOD) bucket classifications for energy and billing.
"""
from __future__ import annotations

import enum


class TimeOfDayBucket(str, enum.Enum):
    """
    TOD bucket for energy accumulation and tariff TOD modifiers.

    Default KSEB windows (configurable via DB):
      DAY   : 06:00 – 18:00  (12 hours)
      PEAK  : 18:00 – 22:00  ( 4 hours, highest tariff multiplier)
      NIGHT : 22:00 – 06:00  ( 8 hours)

    All window boundaries are stored in the DB (tariff_tod_windows table)
    and evaluated server-side against the recording's UTC timestamp
    converted to the device's configured timezone.
    """

    DAY = "DAY"
    PEAK = "PEAK"
    NIGHT = "NIGHT"
