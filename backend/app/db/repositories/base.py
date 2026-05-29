"""
app/db/repositories/base.py
===========================
Generic async repository base class.

Implements the Repository Pattern:
- All DB access goes through typed repository instances.
- Services receive repository objects via dependency injection.
- No raw SQLAlchemy queries escape into the service layer.
- Soft-delete aware: active() scope filters is_deleted=False.

Type parameter T is bound to the SQLAlchemy model class.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async CRUD repository.

    Subclasses must set `model` to the ORM class they manage:

        class DeviceRepository(BaseRepository[Device]):
            model = Device
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    async def get_by_id(self, pk: uuid.UUID) -> ModelT | None:
        """Fetch by primary key; returns None if not found or soft-deleted."""
        stmt = select(self.model).where(
            self.model.id == pk,  # type: ignore[attr-defined]
            self.model.is_deleted == False,  # noqa: E712  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, pk: uuid.UUID) -> ModelT:
        """Fetch by primary key; raises NotFoundError if absent."""
        from app.core.exceptions import NotFoundError

        obj = await self.get_by_id(pk)
        if obj is None:
            raise NotFoundError(
                f"{self.model.__name__} with id={pk} not found.",
                model=self.model.__name__,
                id=str(pk),
            )
        return obj

    async def list_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> list[ModelT]:
        """Return a paginated list of records."""
        stmt = select(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712  # type: ignore[attr-defined]
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, include_deleted: bool = False) -> int:
        """Return total row count."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)  # noqa: E712  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    async def create(self, obj: ModelT) -> ModelT:
        """Persist a new model instance and flush to get server-generated values."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **kwargs: Any) -> ModelT:
        """Update attributes on an existing model instance."""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT) -> ModelT:
        """
        Mark a record as deleted without removing the row.
        Preserves full audit trail.
        """
        obj.is_deleted = True  # type: ignore[attr-defined]
        obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def hard_delete(self, obj: ModelT) -> None:
        """
        Physically remove a row.
        Use only for GDPR erasure or test teardown.
        """
        await self._session.delete(obj)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Session delegation
    # ------------------------------------------------------------------

    async def refresh(self, obj: ModelT) -> ModelT:
        """Reload the object state from the database."""
        await self._session.refresh(obj)
        return obj
