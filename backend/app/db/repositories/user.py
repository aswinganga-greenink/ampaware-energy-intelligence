"""
app/db/repositories/user.py
===========================
User and API Key repositories.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.domain.models.user import User, UserApiKey


class UserRepository(BaseRepository[User]):
    """Repository for managing Users."""

    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Fetch an active user by their email address (case-insensitive)."""
        stmt = select(User).where(
            User.email == email.lower().strip(),
            User.is_deleted == False,  # noqa: E712
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class UserApiKeyRepository(BaseRepository[UserApiKey]):
    """Repository for managing User API Keys."""

    model = UserApiKey

    async def get_active_api_key(self, key_hash: str) -> UserApiKey | None:
        """
        Fetch a valid API key by its hash, eager-loading the associated User.
        A key is valid if it is not revoked and has not expired.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(UserApiKey)
            .options(selectinload(UserApiKey.user))
            .where(
                UserApiKey.key_hash == key_hash,
                UserApiKey.is_revoked == False,  # noqa: E712
                UserApiKey.expires_at > now,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
