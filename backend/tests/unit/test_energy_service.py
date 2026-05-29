"""
tests/unit/test_energy_service.py
"""
from datetime import datetime
from unittest.mock import AsyncMock

from app.domain.enums.time_of_day import TimeOfDayBucket
from app.services.energy import EnergyAggregationService


def test_determine_tod_bucket():
    # We mock out the session since determine_tod_bucket doesn't use it
    service = EnergyAggregationService(session=AsyncMock())

    # KSEB standard:
    # DAY: 6am - 6pm (06:00 - 18:00)
    # PEAK: 6pm - 10pm (18:00 - 22:00)
    # NIGHT: 10pm - 6am (22:00 - 06:00)

    # 10:00 AM IST (we feed UTC datetime that represents 10AM IST)
    # 04:30 UTC = 10:00 IST
    dt_day = datetime.fromisoformat("2026-05-29T04:30:00+00:00")
    assert service.determine_tod_bucket(dt_day) == TimeOfDayBucket.DAY

    # 07:00 PM IST
    # 13:30 UTC = 19:00 IST
    dt_peak = datetime.fromisoformat("2026-05-29T13:30:00+00:00")
    assert service.determine_tod_bucket(dt_peak) == TimeOfDayBucket.PEAK

    # 02:00 AM IST
    # 20:30 UTC = 02:00 IST (next day in IST)
    dt_night = datetime.fromisoformat("2026-05-29T20:30:00+00:00")
    assert service.determine_tod_bucket(dt_night) == TimeOfDayBucket.NIGHT
