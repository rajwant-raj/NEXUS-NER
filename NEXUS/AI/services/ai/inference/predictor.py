"""
NEXUS-NER | Module D — Inference Engine
========================================
Loads the trained model pipeline and exposes a clean predict() interface.

This module is designed to be:
    - Fast   (model loaded once at import time)
    - Safe   (validates all inputs before inference)
    - Simple (one function: predict)

Usage
-----
    from inference.predictor import predict, predict_batch

    result = predict({
        "rainfall_1h": 88,
        "rainfall_3h": 205,
        "rainfall_6h": 280,
        "rainfall_24h": 320,
        "temperature": 19.0,
        "humidity": 92.0,
        "traffic_level": 0.72,
        "average_speed": 28.0,
        "road_condition": 0.32,
        "road_age": 15.0,
        "maintenance_score": 0.40,
        "slope": 18.4,
        "elevation": 1200.0,
        "river_distance": 0.9,
        "historical_incidents": 7,
        "incident_count_7d": 3,
        "incident_count_30d": 9,
        "previous_disruptions": 4,
    })

    # → {"probability": 0.82, "risk_level": "HIGH"}
"""

import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

AI_ROOT    = Path(__file__).resolve().parent.parent
MODEL_PATH = AI_ROOT / "models" / "risk_model.pkl"

sys.path.insert(0, str(AI_ROOT))
from features.feature_engineering import RAW_FEATURE_COLUMNS


# ---------------------------------------------------------------------------
# Input validation schema
# ---------------------------------------------------------------------------

_VALIDATION_RULES: dict[str, dict[str, Any]] = {
    "rainfall_1h":           {"min": 0,    "max": 500,  "type": float},
    "rainfall_3h":           {"min": 0,    "max": 1000, "type": float},
    "rainfall_6h":           {"min": 0,    "max": 1500, "type": float},
    "rainfall_24h":          {"min": 0,    "max": 3000, "type": float},
    "temperature":           {"min": -10,  "max": 50,   "type": float},
    "humidity":              {"min": 0,    "max": 100,  "type": float},
    "traffic_level":         {"min": 0.0,  "max": 1.0,  "type": float},
    "average_speed":         {"min": 0,    "max": 150,  "type": float},
    "road_condition":        {"min": 0.0,  "max": 1.0,  "type": float},
    "road_age":              {"min": 0,    "max": 100,  "type": float},
    "maintenance_score":     {"min": 0.0,  "max": 1.0,  "type": float},
    "slope":                 {"min": 0,    "max": 90,   "type": float},
    "elevation":             {"min": 0,    "max": 8848, "type": float},
    "river_distance":        {"min": 0,    "max": 100,  "type": float},
    "historical_incidents":  {"min": 0,    "max": 9999, "type": int},
    "incident_count_7d":    {"min": 0,    "max": 9999, "type": int},
    "incident_count_30d":   {"min": 0,    "max": 9999, "type": int},
    "previous_disruptions":  {"min": 0,    "max": 9999, "type": int},
}

#: Defaults for optional fields (so the API can accept partial input)
_DEFAULTS: dict[str, Any] = {
    "rainfall_6h":          0.0,
    "rainfall_24h":         0.0,
    "temperature":          22.0,
    "humidity":             70.0,
    "average_speed":        40.0,
    "road_age":             10.0,
    "maintenance_score":    0.70,
    "elevation":            500.0,
    "incident_count_7d":   0,
    "incident_count_30d":  0,
    "previous_disruptions": 0,
}

#: Minimum required fields (cannot be defaulted)
_REQUIRED_FIELDS = {
    "rainfall_1h", "rainfall_3h", "traffic_level",
    "road_condition", "slope", "river_distance",
    "historical_incidents",
}


# ---------------------------------------------------------------------------
# Risk level thresholds
# ---------------------------------------------------------------------------

def _probability_to_risk_level(prob: float) -> str:
    if prob < 0.25:
        return "SAFE"
    elif prob < 0.50:
        return "MODERATE"
    elif prob < 0.75:
        return "HIGH"
    else:
        return "CRITICAL"


# ---------------------------------------------------------------------------
# Model loader (singleton pattern)
# ---------------------------------------------------------------------------

_model = None


def _load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}\n"
                "Run  python training/train.py  first."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def _validate_and_fill(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate raw input dict, fill defaults, return clean dict."""
    # Check required fields
    missing = _REQUIRED_FIELDS - set(raw.keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    # Fill defaults for optional missing fields
    filled = {**_DEFAULTS, **raw}

    # Type-coerce and range-check
    errors = []
    for col, rules in _VALIDATION_RULES.items():
        if col not in filled:
            errors.append(f"'{col}' is missing and has no default")
            continue
        val = filled[col]
        # Coerce
        try:
            filled[col] = rules["type"](val)
        except (TypeError, ValueError):
            errors.append(f"'{col}' cannot be converted to {rules['type'].__name__}: {val!r}")
            continue
        # Range check
        if not (rules["min"] <= filled[col] <= rules["max"]):
            errors.append(
                f"'{col}' = {filled[col]} is outside valid range "
                f"[{rules['min']}, {rules['max']}]"
            )

    if errors:
        raise ValueError("Input validation failed:\n  " + "\n  ".join(errors))

    return filled


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict(features: dict[str, Any]) -> dict[str, Any]:
    """
    Predict disruption probability for a single road segment.

    Parameters
    ----------
    features : dict
        Raw feature values. Required fields: rainfall_1h, rainfall_3h,
        traffic_level, road_condition, slope, river_distance,
        historical_incidents. All other fields have defaults.

    Returns
    -------
    dict with keys:
        probability  – float in [0, 1]
        risk_level   – "SAFE" | "MODERATE" | "HIGH" | "CRITICAL"
    """
    model  = _load_model()
    filled = _validate_and_fill(features)

    # Build a single-row DataFrame in the correct column order
    row = pd.DataFrame([{col: filled[col] for col in RAW_FEATURE_COLUMNS}])

    prob = float(model.predict_proba(row)[0, 1])
    prob = round(min(max(prob, 0.0), 1.0), 4)

    return {
        "probability": prob,
        "risk_level":  _probability_to_risk_level(prob),
    }


def predict_batch(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Predict disruption probability for a list of road segments.

    Parameters
    ----------
    records : list of dicts (same schema as predict())

    Returns
    -------
    list of dicts (same schema as predict() output)
    """
    model = _load_model()
    rows  = []
    for rec in records:
        filled = _validate_and_fill(rec)
        rows.append({col: filled[col] for col in RAW_FEATURE_COLUMNS})

    df = pd.DataFrame(rows)
    probs = model.predict_proba(df)[:, 1]

    return [
        {
            "probability": round(float(p), 4),
            "risk_level":  _probability_to_risk_level(float(p)),
        }
        for p in probs
    ]


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🔍 NEXUS-NER | Inference Engine — Smoke Test")
    print("=" * 50)

    test_cases = [
        {
            "name": "Low-risk (dry day, good road)",
            "input": {
                "rainfall_1h": 5, "rainfall_3h": 10, "traffic_level": 0.20,
                "road_condition": 0.85, "slope": 5.0, "river_distance": 8.0,
                "historical_incidents": 1,
            },
        },
        {
            "name": "High-risk (heavy rain, poor road)",
            "input": {
                "rainfall_1h": 90, "rainfall_3h": 210, "traffic_level": 0.75,
                "road_condition": 0.30, "slope": 18.0, "river_distance": 0.9,
                "historical_incidents": 7,
            },
        },
        {
            "name": "Critical (extreme rain + landslide conditions)",
            "input": {
                "rainfall_1h": 150, "rainfall_3h": 380, "traffic_level": 0.10,
                "road_condition": 0.15, "slope": 40.0, "river_distance": 0.3,
                "historical_incidents": 12,
            },
        },
    ]

    for case in test_cases:
        result = predict(case["input"])
        print(f"\n  Scenario: {case['name']}")
        print(f"    Probability : {result['probability']:.1%}")
        print(f"    Risk Level  : {result['risk_level']}")

    print("\n✅ Inference engine OK")
