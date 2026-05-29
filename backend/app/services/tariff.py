"""
app/services/tariff.py
======================
Service for evaluating and calculating energy costs based on Tariff rules.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TariffNotFoundError
from app.db.repositories.tariff import TariffVersionRepository
from app.domain.models.tariff import TariffVersion


class TariffEngineService:
    """Service to evaluate complex tariff cost logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.tariff_repo = TariffVersionRepository(session)

    async def get_active_tariff(
        self, category_id: uuid.UUID, target_date: date
    ) -> TariffVersion:
        """Fetch the active gazette tariff for a category on a specific date."""
        version = await self.tariff_repo.get_active_version(category_id, target_date)
        if not version:
            raise TariffNotFoundError(
                "No active tariff version found for the given category and date.",
                category_id=str(category_id),
                target_date=target_date.isoformat(),
            )
        return version

    def calculate_base_energy_charge(
        self,
        total_kwh: float,
        tariff_version: TariffVersion,
    ) -> float:
        """
        Calculate the base energy charge across slabs.
        This calculates telescopic (tiered) pricing logic.
        """
        if total_kwh <= 0:
            return 0.0

        slabs = sorted(tariff_version.slabs, key=lambda s: s.slab_order)
        total_charge = 0.0
        remaining_kwh = total_kwh

        for slab in slabs:
            if remaining_kwh <= 0:
                break

            # Calculate how many units fit into this slab
            slab_capacity = (
                (float(slab.units_to) - float(slab.units_from) + 1)
                if slab.units_to is not None
                else float("inf")
            )

            units_in_slab = min(remaining_kwh, slab_capacity)
            total_charge += units_in_slab * float(slab.rate_per_unit)
            remaining_kwh -= units_in_slab

        return total_charge
