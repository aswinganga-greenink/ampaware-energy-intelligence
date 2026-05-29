"""
app/domain/enums/user_role.py
==============================
RBAC role definitions for the platform.
"""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """
    Platform-level user roles.

    ADMIN    — full system access: tariff management, device provisioning,
               all analytics, user management
    OPERATOR — can manage devices and view analytics; cannot manage users/tariffs
    CONSUMER — can view only their own devices, billing, and analytics
    """

    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    CONSUMER = "CONSUMER"
