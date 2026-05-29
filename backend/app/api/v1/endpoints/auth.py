"""
app/api/v1/endpoints/auth.py
============================
User authentication and JWT issuance.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, verify_password
from app.db.repositories.user import UserRepository
from app.domain.models.user import User

router = APIRouter(tags=["auth"])


@router.post("/login", summary="Login with username (email) and password to get a JWT.")
async def login_access_token(
    session: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, str]:
    """
    OAuth2 compatible token login, getting an access token for future requests.
    - username must be the user's email.
    """
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(form_data.username)
    if not user:
        raise AuthenticationError("Incorrect email or password")

    if not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError("Incorrect email or password")

    if not user.is_active:
        raise AuthenticationError("Inactive user account")

    access_token = create_access_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", summary="Get the current authenticated user's profile.")
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return the profile of the currently authenticated user."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
    }
