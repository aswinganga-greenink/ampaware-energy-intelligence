"""
tests/unit/test_tariff_service.py
"""
from unittest.mock import AsyncMock

from app.domain.models.tariff import TariffSlab, TariffVersion
from app.services.tariff import TariffEngineService


def test_calculate_base_energy_charge_telescopic():
    service = TariffEngineService(session=AsyncMock())

    version = TariffVersion()
    s1 = TariffSlab(
        units_from=1,
        units_to=50,
        rate_per_unit=3.0,
        slab_order=1,
    )
    s2 = TariffSlab(
        units_from=51,
        units_to=100,
        rate_per_unit=4.0,
        slab_order=2,
    )
    s3 = TariffSlab(
        units_from=101,
        units_to=None,
        rate_per_unit=5.0,
        slab_order=3,
    )
    version.slabs = [s1, s2, s3]

    # For 20 KWh -> 20 * 3.0 = 60.0
    assert service.calculate_base_energy_charge(20.0, version) == 60.0

    # For 70 KWh -> (50 * 3.0) + (20 * 4.0) = 150 + 80 = 230.0
    # Capacity slab 1: 50 - 1 + 1 = 50 units.
    # Capacity slab 2: 100 - 51 + 1 = 50 units.
    assert service.calculate_base_energy_charge(70.0, version) == 230.0

    # For 120 KWh -> (50 * 3.0) + (50 * 4.0) + (20 * 5.0) = 150 + 200 + 100 = 450.0
    assert service.calculate_base_energy_charge(120.0, version) == 450.0

