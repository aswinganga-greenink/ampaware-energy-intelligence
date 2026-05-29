"""
app/domain/enums/anomaly_type.py
=================================
Types of anomalies detected by the health monitoring engine.
"""
from __future__ import annotations

import enum


class AnomalyType(str, enum.Enum):
    """
    Classification of detected electrical anomalies.
    """

    # Voltage anomalies
    VOLTAGE_HIGH = "VOLTAGE_HIGH"           # voltage > upper threshold
    VOLTAGE_LOW = "VOLTAGE_LOW"             # voltage < lower threshold
    VOLTAGE_SPIKE = "VOLTAGE_SPIKE"         # instantaneous spike
    VOLTAGE_SAG = "VOLTAGE_SAG"             # momentary dip

    # Current anomalies
    CURRENT_HIGH = "CURRENT_HIGH"           # overcurrent condition
    CURRENT_UNBALANCE = "CURRENT_UNBALANCE" # phase currents differ by > threshold

    # Power factor
    POWER_FACTOR_LOW = "POWER_FACTOR_LOW"   # PF < configured threshold
    POWER_FACTOR_LEADING = "POWER_FACTOR_LEADING"   # leading PF (capacitive)

    # Phase anomalies (three-phase only)
    PHASE_IMBALANCE = "PHASE_IMBALANCE"     # voltage imbalance between phases
    PHASE_LOSS = "PHASE_LOSS"               # one phase has no voltage/current

    # Availability
    OUTAGE = "OUTAGE"                        # no readings for > threshold period
    METER_OFFLINE = "METER_OFFLINE"         # device stopped sending heartbeats

    # Meter health
    METER_DRIFT = "METER_DRIFT"             # readings drift from calibration ref
    SENSOR_FAILURE = "SENSOR_FAILURE"       # sensor returning impossible values
    CLOCK_DRIFT = "CLOCK_DRIFT"             # device clock significantly off

    # Data quality
    DUPLICATE_PACKETS = "DUPLICATE_PACKETS"
    OUT_OF_ORDER_PACKETS = "OUT_OF_ORDER_PACKETS"
    CORRUPTED_PAYLOAD = "CORRUPTED_PAYLOAD"


class AnomalySeverity(str, enum.Enum):
    """
    Severity classification for triaging alerts.

    LOW      — informational, no immediate action needed
    MEDIUM   — investigate within 24 hours
    HIGH     — investigate within 1 hour
    CRITICAL — requires immediate action (potential safety risk)
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
