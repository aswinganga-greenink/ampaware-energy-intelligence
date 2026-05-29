"""
app/db/repositories/tariff.py
=============================
Repositories for Tariff configurations and gazette versions.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.domain.models.tariff import (
    TariffCategory,
    TariffSlab,
    TariffTodModifier,
    TariffTodWindow,
    TariffVersion,
)


class TariffCategoryRepository(BaseRepository[TariffCategory]):
    """Repository for Tariff Categories (e.g., Domestic, Industrial)."""

    model = TariffCategory


class TariffVersionRepository(BaseRepository[TariffVersion]):
    """Repository for Date-bound Tariff Versions."""

    model = TariffVersion

    async def get_active_version(
        self, category_id: uuid.UUID, target_date: date
    ) -> TariffVersion | None:
        """
        Fetch the active tariff version for a category on a given date.
        Eagerly loads slabs, TOD windows, and TOD modifiers for calculation.
        """
        stmt = (
            select(TariffVersion)
            .options(
                selectinload(TariffVersion.slabs),
                selectinload(TariffVersion.tod_windows),
                selectinload(TariffVersion.tod_modifiers),
            )
            .where(
                TariffVersion.category_id == category_id,
                TariffVersion.effective_from <= target_date,
                (TariffVersion.effective_to >= target_date)
                | (TariffVersion.effective_to.is_(None)),
                TariffVersion.is_deleted == False,  # noqa: E712
            )
            .order_by(TariffVersion.effective_from.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class TariffSlabRepository(BaseRepository[TariffSlab]):
    """Repository for Tariff Slabs."""

    model = TariffSlab


class TariffTodWindowRepository(BaseRepository[TariffTodWindow]):
    """Repository for Time of Day Windows."""

    model = TariffTodWindow


class TariffTodModifierRepository(BaseRepository[TariffTodModifier]):
    """Repository for Time of Day Modifiers."""

    model = TariffTodModifier
