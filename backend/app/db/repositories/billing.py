"""
app/db/repositories/billing.py
==============================
Repository for Billing Snapshots.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.domain.models.billing import BillingSnapshot


class BillingSnapshotRepository(BaseRepository[BillingSnapshot]):
    """Repository for managing immutable Billing Snapshots."""

    model = BillingSnapshot

    async def get_snapshots_in_period(
        self, device_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[BillingSnapshot]:
        """Fetch billing snapshots for a device within a given period."""
        stmt = (
            select(BillingSnapshot)
            .where(
                BillingSnapshot.device_id == device_id,
                BillingSnapshot.billing_period_start >= start_date,
                BillingSnapshot.billing_period_start <= end_date,
            )
            .order_by(BillingSnapshot.billing_period_start.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
