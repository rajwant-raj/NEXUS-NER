"""
NEXUS-NER | Module F — Explainability Engine
=============================================
Explains WHY the model considers a road segment risky by ranking the
top contributing features in human-readable language.

Approach
--------
Primary  : Random Forest feature importances weighted by actual input values.
           This is fast, transparent, and always available.
Optional : SHAP TreeExplainer — import shap if installed for instance-level
           explanations (more accurate but slower).

Output example
--------------
    {
      "factors": [
          "Heavy rainfall (88 mm/h)",
          "Poor road condition (score: 0.32)",
          "High historical incident frequency (7 incidents)",
          "Steep terrain (slope: 18.4°)"
      ]
    }

Usage
-----
    from explainability.explainer import explain

    result = explain(features_dict, ml_probability=0.82)
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Any

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

from features.feature_engineering import FEATURE_COLUMNS


# ---------------------------------------------------------------------------
# Human-readable factor descriptions
# ---------------------------------------------------------------------------

def _describe_factor(feature: str, value: float, contribution: float) -> str | None:
    """
    Convert a (feature, value, contribution) triple into a readable string.
    Returns None if the factor is not significant enough to mention.
    """
    if contribution < 0.02:   # ignore tiny contributions
        return None

    mapping = {
        "rainfall_1h": (
            lambda v: f"Heavy rainfall ({v:.0f} mm/h)" if v > 50
            else (f"Moderate rainfall ({v:.0f} mm/h)" if v > 15 else None)
        ),
        "rainfall_3h": (
            lambda v: f"High 3-hour rainfall accumulation ({v:.0f} mm)" if v > 100 else None
        ),
        "rainfall_24h": (
            lambda v: f"Very high 24-hour rainfall ({v:.0f} mm)" if v > 200 else None
        ),
        "rainfall_intensity": (
            lambda v: f"Intense rainfall rate ({v:.2f} ratio)" if v > 0.3 else None
        ),
        "rainfall_accumulation": (
            lambda v: f"High rainfall accumulation ({v:.0f} mm)" if v > 150 else None
        ),
        "road_condition": (
            lambda v: f"Poor road condition (score: {v:.2f})" if v < 0.4
            else (f"Moderate road condition (score: {v:.2f})" if v < 0.65 else None)
        ),
        "road_condition_score": (
            lambda v: f"Deteriorated road surface (composite score: {v:.2f})" if v < 0.3 else None
        ),
        "maintenance_score": (
            lambda v: f"Inadequate road maintenance (score: {v:.2f})" if v < 0.4 else None
        ),
        "road_age": (
            lambda v: f"Aging road infrastructure ({v:.0f} years old)" if v > 20 else None
        ),
        "slope": (
            lambda v: f"Steep terrain (slope: {v:.1f}°)" if v > 15
            else (f"Moderate slope ({v:.1f}°)" if v > 8 else None)
        ),
        "terrain_risk": (
            lambda v: f"High terrain risk (composite: {v:.2f})" if v > 0.5 else None
        ),
        "river_distance": (
            lambda v: f"Road runs close to a river ({v:.1f} km)" if v < 2.0 else None
        ),
        "elevation": (
            lambda v: f"High altitude section ({v:.0f} m)" if v > 2000 else None
        ),
        "traffic_level": (
            lambda v: f"High traffic congestion (level: {v:.0%})" if v > 0.6 else None
        ),
        "congestion_score": (
            lambda v: f"Severe traffic congestion (score: {v:.2f})" if v > 0.5 else None
        ),
        "historical_incidents": (
            lambda v: f"High historical incident frequency ({int(v)} incidents)" if v > 5 else
            (f"Moderate historical incidents ({int(v)})" if v > 2 else None)
        ),
        "historical_risk": (
            lambda v: f"Elevated historical risk pattern (score: {v:.2f})" if v > 0.4 else None
        ),
        "incident_count_7d": (
            lambda v: f"Recent incidents in past 7 days ({int(v)} recorded)" if v >= 2 else None
        ),
        "incident_count_30d": (
            lambda v: f"High incident count in past 30 days ({int(v)} recorded)" if v > 4 else None
        ),
        "disruption_frequency": (
            lambda v: f"History of frequent disruptions (rate: {v:.3f}/year)" if v > 0.2 else None
        ),
        "humidity": (
            lambda v: f"Very high humidity ({v:.0f}%)" if v > 90 else None
        ),
    }

    fn = mapping.get(feature)
    if fn is None:
        return None
    return fn(value)


# ---------------------------------------------------------------------------
# Core explainer
# ---------------------------------------------------------------------------

def explain(
    features: dict[str, Any],
    ml_probability: float,
    top_n: int = 5,
    use_shap: bool = False,
) -> dict[str, Any]:
    """
    Explain the model's disruption prediction for a given road segment.

    Parameters
    ----------
    features       : dict — same raw feature dict passed to predictor.predict()
    ml_probability : float — model probability (from predictor.predict())
    top_n          : int   — maximum number of factors to return
    use_shap       : bool  — attempt to use SHAP (falls back silently)

    Returns
    -------
    dict with keys:
        factors      – list of human-readable factor strings (max top_n)
        raw_scores   – dict mapping feature → contribution score (for debugging)
        method       – "feature_importance" | "shap"
    """
    method = "feature_importance"

    # ── Optional SHAP path ──────────────────────────────────────────────────
    if use_shap:
        try:
            result = _explain_with_shap(features, ml_probability, top_n)
            if result:
                return result
        except Exception:
            pass   # fall through to feature-importance approach

    # ── Feature-importance-based explanation ─────────────────────────────────
    return _explain_with_importance(features, ml_probability, top_n)


def _explain_with_importance(
    features: dict[str, Any],
    ml_probability: float,
    top_n: int,
) -> dict[str, Any]:
    """
    Use Random Forest feature importances × normalised input value as a
    proxy for feature contribution.
    """
    import joblib
    import numpy as np
    import pandas as pd

    from inference.predictor import _validate_and_fill, _DEFAULTS
    from features.feature_engineering import engineer_features, RAW_FEATURE_COLUMNS

    model_path = AI_ROOT / "models" / "risk_model.pkl"
    if not model_path.exists():
        # Model not trained yet — return heuristic explanation
        return _heuristic_explain(features, ml_probability, top_n)

    pipeline = joblib.load(model_path)
    clf_step = pipeline.named_steps.get("clf")

    # Fill defaults + build row
    filled = {**_DEFAULTS, **features}
    row = pd.DataFrame([{col: filled.get(col, 0) for col in RAW_FEATURE_COLUMNS}])

    # Get engineered feature values
    engineer = pipeline.named_steps.get("engineer")
    if engineer is None:
        return _heuristic_explain(features, ml_probability, top_n)

    feat_values = engineer.transform(row)[0]   # shape (n_features,)

    # Get feature importances
    has_importance = hasattr(clf_step, "feature_importances_")
    if has_importance:
        importances = clf_step.feature_importances_
    else:
        # Logistic regression: use |coefficient| as proxy importance
        if hasattr(clf_step, "coef_"):
            importances = np.abs(clf_step.coef_[0])
        else:
            return _heuristic_explain(features, ml_probability, top_n)

    # Contribution = importance × |value| (normalised)
    max_vals = np.abs(feat_values).max() or 1.0
    norm_vals = np.abs(feat_values) / max_vals
    contributions = importances * norm_vals

    # Sort descending
    ranked = sorted(
        zip(FEATURE_COLUMNS, feat_values, contributions),
        key=lambda x: x[2],
        reverse=True,
    )

    raw_scores = {f: round(float(c), 4) for f, _, c in ranked}

    factors = []
    for feat, val, contrib in ranked:
        if len(factors) >= top_n:
            break
        desc = _describe_factor(feat, float(val), float(contrib))
        if desc and desc not in factors:
            factors.append(desc)

    # Fallback: if no meaningful factors found
    if not factors:
        return _heuristic_explain(features, ml_probability, top_n)

    return {
        "factors":    factors,
        "raw_scores": raw_scores,
        "method":     "feature_importance",
    }


def _heuristic_explain(
    features: dict[str, Any],
    ml_probability: float,
    top_n: int,
) -> dict[str, Any]:
    """
    Rule-based explanation — used when the model isn't available yet
    or as a final fallback.
    """
    candidates = []

    r1h  = float(features.get("rainfall_1h", 0))
    r3h  = float(features.get("rainfall_3h", 0))
    rc   = float(features.get("road_condition", 1))
    sl   = float(features.get("slope", 0))
    rd   = float(features.get("river_distance", 10))
    hi   = int(features.get("historical_incidents", 0))
    tl   = float(features.get("traffic_level", 0))
    ms   = float(features.get("maintenance_score", 1))

    if r1h > 50:
        candidates.append((r1h,        f"Heavy rainfall ({r1h:.0f} mm/h)"))
    elif r1h > 15:
        candidates.append((r1h * 0.5,  f"Moderate rainfall ({r1h:.0f} mm/h)"))

    if r3h > 100:
        candidates.append((r3h * 0.4,  f"High 3-hour rainfall accumulation ({r3h:.0f} mm)"))

    if rc < 0.4:
        candidates.append(((1 - rc),   f"Poor road condition (score: {rc:.2f})"))
    elif rc < 0.6:
        candidates.append(((1 - rc) * 0.6, f"Moderate road condition (score: {rc:.2f})"))

    if sl > 15:
        candidates.append((sl / 60,    f"Steep terrain (slope: {sl:.1f}°)"))

    if rd < 2.0:
        candidates.append((1 / (rd + 0.5), f"Road runs close to a river ({rd:.1f} km)"))

    if hi > 5:
        candidates.append((hi / 10,    f"High historical incident frequency ({hi} incidents)"))

    if tl > 0.6:
        candidates.append((tl,         f"High traffic congestion (level: {tl:.0%})"))

    if ms < 0.4:
        candidates.append(((1 - ms),   f"Inadequate road maintenance (score: {ms:.2f})"))

    # Sort by score descending, take top_n
    candidates.sort(key=lambda x: x[0], reverse=True)
    factors = [desc for _, desc in candidates[:top_n]]

    if not factors:
        if ml_probability > 0.5:
            factors = ["Combination of unfavourable environmental conditions"]
        else:
            factors = ["No significant risk factors identified"]

    return {
        "factors": factors,
        "raw_scores": {},
        "method": "heuristic",
    }


def _explain_with_shap(
    features: dict[str, Any],
    ml_probability: float,
    top_n: int,
) -> dict[str, Any] | None:
    """Attempt SHAP-based explanation. Returns None if SHAP not available."""
    try:
        import shap
        import joblib
        import pandas as pd
        from inference.predictor import _validate_and_fill
        from features.feature_engineering import (
            engineer_features, RAW_FEATURE_COLUMNS
        )

        model_path = AI_ROOT / "models" / "risk_model.pkl"
        if not model_path.exists():
            return None

        pipeline = joblib.load(model_path)
        clf = pipeline.named_steps.get("clf")
        engineer = pipeline.named_steps.get("engineer")
        if clf is None or engineer is None:
            return None

        # Build engineered features
        from inference.predictor import _DEFAULTS
        filled = {**_DEFAULTS, **features}
        row = pd.DataFrame([{col: filled.get(col, 0) for col in RAW_FEATURE_COLUMNS}])
        feat_values = engineer.transform(row)
        feat_df = pd.DataFrame(feat_values, columns=FEATURE_COLUMNS)

        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(feat_df)

        # shap_values[1] = contributions toward class 1 (disruption)
        sv = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]

        ranked = sorted(
            zip(FEATURE_COLUMNS, feat_df.values[0], sv),
            key=lambda x: abs(x[2]),
            reverse=True,
        )

        raw_scores = {f: round(float(s), 4) for f, _, s in ranked}
        factors = []
        for feat, val, score in ranked:
            if len(factors) >= top_n:
                break
            if score > 0:   # positive = increases risk
                desc = _describe_factor(feat, float(val), abs(float(score)))
                if desc and desc not in factors:
                    factors.append(desc)

        return {
            "factors":    factors or ["No dominant risk factor identified"],
            "raw_scores": raw_scores,
            "method":     "shap",
        }
    except ImportError:
        return None   # SHAP not installed
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🔍 NEXUS-NER | Explainability — Smoke Test")
    print("=" * 50)

    test_input = {
        "rainfall_1h": 88, "rainfall_3h": 205,
        "traffic_level": 0.72, "road_condition": 0.32,
        "slope": 18.4, "historical_incidents": 7,
        "river_distance": 0.9, "maintenance_score": 0.38,
    }

    result = explain(test_input, ml_probability=0.82)
    print(f"\n  ML Probability : 82%")
    print(f"  Method         : {result['method']}")
    print(f"\n  Top Factors:")
    for i, factor in enumerate(result["factors"], 1):
        print(f"    {i}. {factor}")

    print("\n✅ Explainability OK")
