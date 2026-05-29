"""
app/domain/enums/connection_type.py
====================================
Connection / phase configuration type for a smart meter device.
"""
from __future__ import annotations

import enum


class ConnectionType(str, enum.Enum):
    """
    Electrical connection type of the metered installation.

    SINGLE_PHASE         — standard residential, 1 live + neutral
    THREE_PHASE_BALANCED — industrial/commercial, all 3 phases equal load
    THREE_PHASE_UNBALANCED — industrial, each phase tracked independently
    """

    SINGLE_PHASE = "SINGLE_PHASE"
    THREE_PHASE_BALANCED = "THREE_PHASE_BALANCED"
    THREE_PHASE_UNBALANCED = "THREE_PHASE_UNBALANCED"
