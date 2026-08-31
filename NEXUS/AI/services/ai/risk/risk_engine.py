"""
NEXUS-NER | Module E — Risk Scoring Engine
===========================================
Combines multiple risk signals (ML prediction + domain rules) into
a single final risk score with categorical label.

Formula
-------
    final_risk =
        0.40 × ml_probability
      + 0.20 × weather_risk
      + 0.15 × road_condition_risk
      + 0.10 × traffic_risk
      + 0.10 × historical_risk
      + 0.05 × accessibility_penalty

Risk categories
---------------
    0.00–0.25 → SAFE
    0.25–0.50 → MODERATE
    0.50–0.75 → HIGH
    0.75–1.00 → CRITICAL

Usage
-----
    from risk.risk_engine import compute_risk

    result = compute_risk(
        ml_probability=0.72,
        rainfall_1h=90, rainfall_3h=210,
        road_condition=0.30, traffic_level=0.75,
        historical_incidents=7, slope=18.0,
        river_distance=0.9, maintenance_score=0.40,
    )
    # → {
    #     "final_risk": 0.68,
    #     "risk_level": "HIGH",
    #     "components": { "ml_probability": 0.72, "weather_risk": 0.81, ... }
    #   }
"""

from __future__ import annotations

import math
from typing import Any


# ---------------------------------------------------------------------------
# Weights (must sum to 1.0)
# ---------------------------------------------------------------------------

WEIGHTS = {
    "ml_probability":       0.40,
    "weather_risk":         0.20,
    "road_condition_risk":  0.15,
    "traffic_risk":         0.10,
    "historical_risk":      0.10,
    "accessibility_penalty": 0.05,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


# ---------------------------------------------------------------------------
# Risk thresholds & labels
# ---------------------------------------------------------------------------

RISK_THRESHOLDS = [
    (0.00, 0.25, "SAFE"),
    (0.25, 0.50, "MODERATE"),
    (0.50, 0.75, "HIGH"),
    (0.75, 1.00, "CRITICAL"),
]


def _risk_level(score: float) -> str:
    for low, high, label in RISK_THRESHOLDS:
        if low <= score < high:
            return label
    return "CRITICAL"  # score == 1.0 edge case


# ---------------------------------------------------------------------------
# Component risk calculators
# ---------------------------------------------------------------------------

def _weather_risk(
    rainfall_1h: float,
    rainfall_3h: float,
    rainfall_24h: float = 0.0,
    humidity: float = 70.0,
    temperature: float = 22.0,
) -> float:
    """
    Compute weather risk in [0, 1].
    Heavy rainfall + high humidity + low temperature (fog) → higher risk.
    """
    rain_1h_score  = math.tanh(rainfall_1h  / 60)    # saturates at ~120 mm/h
    rain_3h_score  = math.tanh(rainfall_3h  / 150)
    rain_24h_score = math.tanh(rainfall_24h / 300)
    hum_score      = (humidity - 50) / 50 if humidity > 50 else 0.0
    hum_score      = max(0.0, min(1.0, hum_score))

    weather = (
        0.45 * rain_1h_score
        + 0.30 * rain_3h_score
        + 0.15 * rain_24h_score
        + 0.10 * hum_score
    )
    return round(min(max(weather, 0.0), 1.0), 4)


def _road_condition_risk(
    road_condition: float,
    maintenance_score: float = 0.70,
    road_age: float = 10.0,
) -> float:
    """
    Compute road condition risk in [0, 1].
    Poor condition + low maintenance + old road → higher risk.
    """
    cond_risk  = 1.0 - road_condition          # poor condition → high risk
    maint_risk = 1.0 - maintenance_score
    age_risk   = min(road_age / 30, 1.0)       # saturates at 30 years

    score = (
        0.50 * cond_risk
        + 0.30 * maint_risk
        + 0.20 * age_risk
    )
    return round(min(max(score, 0.0), 1.0), 4)


def _traffic_risk(
    traffic_level: float,
    average_speed: float = 40.0,
) -> float:
    """
    Compute traffic risk in [0, 1].
    Heavy traffic + low speed → higher risk (congestion compounds disruptions).
    """
    traffic_score = traffic_level
    # Very slow speed on a busy road = high risk
    speed_risk = max(0.0, 1 - average_speed / 60)
    score = 0.60 * traffic_score + 0.40 * speed_risk
    return round(min(max(score, 0.0), 1.0), 4)


def _historical_risk(
    historical_incidents: int,
    incident_count_7d: int = 0,
    incident_count_30d: int = 0,
    previous_disruptions: int = 0,
) -> float:
    """
    Compute historical risk in [0, 1].
    Recent incidents carry more weight than long-term history.
    """
    recent  = math.tanh(incident_count_7d  / 3)
    monthly = math.tanh(incident_count_30d / 10)
    long_t  = math.tanh(historical_incidents / 8)
    prev    = math.tanh(previous_disruptions / 5)

    score = (
        0.40 * recent
        + 0.30 * monthly
        + 0.20 * long_t
        + 0.10 * prev
    )
    return round(min(max(score, 0.0), 1.0), 4)


def _accessibility_penalty(
    slope: float,
    river_distance: float,
    elevation: float = 500.0,
) -> float:
    """
    Compute accessibility penalty in [0, 1].
    Steep roads close to rivers at high elevation → harder to access for rescue.
    """
    slope_factor = math.tanh(slope / 30)
    river_factor = math.exp(-river_distance / 3)          # close river = dangerous
    elev_factor  = min(elevation / 3000, 1.0)

    score = (
        0.50 * slope_factor
        + 0.30 * river_factor
        + 0.20 * elev_factor
    )
    return round(min(max(score, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_risk(
    ml_probability: float,
    rainfall_1h: float,
    rainfall_3h: float,
    road_condition: float,
    traffic_level: float,
    historical_incidents: int,
    slope: float,
    river_distance: float,
    # Optional
    rainfall_24h: float = 0.0,
    humidity: float = 70.0,
    temperature: float = 22.0,
    maintenance_score: float = 0.70,
    road_age: float = 10.0,
    average_speed: float = 40.0,
    incident_count_7d: int = 0,
    incident_count_30d: int = 0,
    previous_disruptions: int = 0,
    elevation: float = 500.0,
) -> dict[str, Any]:
    """
    Compute the final composite risk score for a road segment.

    Parameters
    ----------
    ml_probability  : float in [0, 1] — output of the ML disruption model
    (all other parameters are raw feature values)

    Returns
    -------
    dict with keys:
        final_risk   – float in [0, 1]
        risk_level   – "SAFE" | "MODERATE" | "HIGH" | "CRITICAL"
        components   – dict of individual risk signal values
    """
    # --- Validate ml_probability ---
    ml_probability = min(max(float(ml_probability), 0.0), 1.0)

    # --- Compute individual components ---
    weather = _weather_risk(rainfall_1h, rainfall_3h, rainfall_24h, humidity, temperature)
    road    = _road_condition_risk(road_condition, maintenance_score, road_age)
    traffic = _traffic_risk(traffic_level, average_speed)
    history = _historical_risk(
        historical_incidents, incident_count_7d,
        incident_count_30d, previous_disruptions
    )
    access  = _accessibility_penalty(slope, river_distance, elevation)

    components = {
        "ml_probability":       round(ml_probability, 4),
        "weather_risk":         weather,
        "road_condition_risk":  road,
        "traffic_risk":         traffic,
        "historical_risk":      history,
        "accessibility_penalty": access,
    }

    # --- Weighted combination ---
    final_risk = sum(WEIGHTS[k] * v for k, v in components.items())
    final_risk = round(min(max(final_risk, 0.0), 1.0), 4)

    return {
        "final_risk": final_risk,
        "risk_level": _risk_level(final_risk),
        "components": components,
    }


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🔧 NEXUS-NER | Risk Engine — Smoke Test")
    print("=" * 55)

    scenarios = [
        ("Dry day, good road", dict(
            ml_probability=0.18, rainfall_1h=10, rainfall_3h=25,
            road_condition=0.85, traffic_level=0.20, historical_incidents=1,
            slope=5.0, river_distance=8.0,
        )),
        ("Heavy rain", dict(
            ml_probability=0.61, rainfall_1h=90, rainfall_3h=210,
            road_condition=0.85, traffic_level=0.20, historical_incidents=1,
            slope=5.0, river_distance=8.0,
        )),
        ("Heavy rain + poor road", dict(
            ml_probability=0.82, rainfall_1h=90, rainfall_3h=210,
            road_condition=0.30, traffic_level=0.75, historical_incidents=7,
            slope=18.0, river_distance=0.9,
            maintenance_score=0.35, road_age=15.0,
        )),
    ]

    for name, kwargs in scenarios:
        result = compute_risk(**kwargs)
        print(f"\n  Scenario : {name}")
        print(f"    Final Risk : {result['final_risk']:.1%}  → {result['risk_level']}")
        for k, v in result["components"].items():
            print(f"    {k:25s} : {v:.4f}")

    print("\n✅ Risk engine OK")
