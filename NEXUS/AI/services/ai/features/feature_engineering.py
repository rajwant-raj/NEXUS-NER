"""
NEXUS-NER | Module B — Feature Engineering Pipeline
====================================================
Transforms raw input columns into model-ready features.

Exported symbols
----------------
    FEATURE_COLUMNS         – ordered list of final feature names
    build_feature_pipeline  – returns a fitted sklearn Pipeline
    engineer_features       – convenience wrapper (DataFrame → DataFrame)

Usage
-----
    from features.feature_engineering import engineer_features, FEATURE_COLUMNS

    df_raw = pd.read_csv("data/processed/dataset.csv")
    df_feat = engineer_features(df_raw)          # returns engineered DataFrame
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Feature column registry
# ---------------------------------------------------------------------------

#: Raw input columns required for feature engineering
RAW_FEATURE_COLUMNS = [
    "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_24h",
    "temperature", "humidity",
    "traffic_level", "average_speed",
    "road_condition", "road_age", "maintenance_score",
    "slope", "elevation", "river_distance",
    "historical_incidents", "incident_count_7d", "incident_count_30d",
    "previous_disruptions",
]

#: Final engineered feature names (order matches transformer output)
FEATURE_COLUMNS = [
    # Weather
    "rainfall_1h",
    "rainfall_3h",
    "rainfall_24h",
    "rainfall_intensity",       # rainfall_1h / (rainfall_24h + 1)
    "rainfall_accumulation",    # rainfall_3h + rainfall_6h
    "rainfall_change",          # rainfall_3h - rainfall_1h
    "humidity",
    "temperature",
    # Traffic
    "traffic_level",
    "congestion_score",         # traffic_level × (1 - avg_speed/80)
    "speed_deviation",          # |avg_speed - expected_speed_for_traffic|
    # Road
    "road_condition",
    "road_condition_score",     # composite: road_condition × maintenance_score
    "road_age",
    "maintenance_score",
    # Terrain
    "slope",
    "elevation",
    "river_distance",
    "terrain_risk",             # composite: slope/60 + (1-river_distance/20).clip
    # Historical
    "historical_incidents",
    "incident_count_7d",
    "incident_count_30d",
    "incident_frequency",       # incident_count_7d / 7
    "disruption_frequency",     # previous_disruptions / (road_age + 1)
    "historical_risk",          # composite normalised historical signal
]


# ---------------------------------------------------------------------------
# Custom transformer
# ---------------------------------------------------------------------------

class RoadFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Sklearn-compatible transformer that creates domain-specific features
    for road disruption prediction.

    Input  : pandas DataFrame with RAW_FEATURE_COLUMNS present
    Output : numpy ndarray with columns ordered as FEATURE_COLUMNS
    """

    def fit(self, X, y=None):  # noqa: N803
        # Stateless transformer — nothing to fit
        return self

    def transform(self, X, y=None):  # noqa: N803
        if isinstance(X, np.ndarray):
            raise ValueError("Input must be a pandas DataFrame with named columns.")

        df = X.copy()
        out = pd.DataFrame(index=df.index)

        # ── Weather features ────────────────────────────────────────────────
        out["rainfall_1h"]         = df["rainfall_1h"]
        out["rainfall_3h"]         = df["rainfall_3h"]
        out["rainfall_24h"]        = df["rainfall_24h"]
        out["rainfall_intensity"]  = df["rainfall_1h"] / (df["rainfall_24h"] + 1)
        out["rainfall_accumulation"] = df["rainfall_3h"] + df.get("rainfall_6h", df["rainfall_3h"])
        out["rainfall_change"]     = df["rainfall_3h"] - df["rainfall_1h"]
        out["humidity"]            = df["humidity"]
        out["temperature"]         = df["temperature"]

        # ── Traffic features ─────────────────────────────────────────────────
        avg_speed = df["average_speed"]
        traffic   = df["traffic_level"]

        out["traffic_level"]    = traffic
        out["congestion_score"] = traffic * (1 - (avg_speed / 80).clip(0, 1))

        # Expected speed given traffic (linear model: 60 km/h at traffic=0)
        expected_speed = 60 * (1 - traffic)
        out["speed_deviation"]  = np.abs(avg_speed - expected_speed)

        # ── Road features ─────────────────────────────────────────────────────
        rc = df["road_condition"]
        ms = df["maintenance_score"]
        age = df["road_age"]

        out["road_condition"]       = rc
        out["road_condition_score"] = rc * ms            # high only when both good
        out["road_age"]             = age
        out["maintenance_score"]    = ms

        # ── Terrain features ──────────────────────────────────────────────────
        slope     = df["slope"]
        elev      = df["elevation"]
        river     = df["river_distance"]

        out["slope"]          = slope
        out["elevation"]      = elev
        out["river_distance"] = river

        slope_norm  = (slope / 60).clip(0, 1)
        river_norm  = (1 - (river / 20)).clip(0, 1)   # closer river → higher risk
        out["terrain_risk"] = (0.6 * slope_norm + 0.4 * river_norm).clip(0, 1)

        # ── Historical features ────────────────────────────────────────────────
        hist = df["historical_incidents"]
        i7d  = df["incident_count_7d"]
        i30d = df["incident_count_30d"]
        prev = df["previous_disruptions"]

        out["historical_incidents"] = hist
        out["incident_count_7d"]   = i7d
        out["incident_count_30d"]  = i30d
        out["incident_frequency"]  = i7d / 7.0
        out["disruption_frequency"] = prev / (age + 1)
        out["historical_risk"]     = (
            np.tanh(i7d / 3) * 0.5
            + np.tanh(hist / 8) * 0.3
            + np.tanh(prev / 5) * 0.2
        )

        # Ensure column order matches FEATURE_COLUMNS
        return out[FEATURE_COLUMNS].values.astype(np.float64)

    def get_feature_names_out(self, input_features=None):
        return np.array(FEATURE_COLUMNS)


# ---------------------------------------------------------------------------
# Pipeline builder
# ---------------------------------------------------------------------------

def build_feature_pipeline(scale: bool = True) -> Pipeline:
    """
    Build a sklearn Pipeline:
        RoadFeatureEngineer → [StandardScaler]

    Parameters
    ----------
    scale : bool
        Whether to apply StandardScaler after feature engineering.
        Set False when using tree-based models (they don't need scaling)
        but True when using logistic regression.

    Returns
    -------
    sklearn.pipeline.Pipeline
    """
    steps = [("engineer", RoadFeatureEngineer())]
    if scale:
        steps.append(("scaler", StandardScaler()))
    return Pipeline(steps)


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame, scale: bool = False) -> pd.DataFrame:
    """
    Apply feature engineering to a raw DataFrame and return a new DataFrame
    with FEATURE_COLUMNS as columns.

    Parameters
    ----------
    df    : pd.DataFrame — raw dataset with RAW_FEATURE_COLUMNS
    scale : bool         — whether to apply StandardScaler

    Returns
    -------
    pd.DataFrame with columns = FEATURE_COLUMNS
    """
    pipeline = build_feature_pipeline(scale=scale)
    arr = pipeline.fit_transform(df)
    return pd.DataFrame(arr, columns=FEATURE_COLUMNS, index=df.index)


# ---------------------------------------------------------------------------
# Quick smoke-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🔧 NEXUS-NER | Feature Engineering — Smoke Test")
    print("=" * 50)

    # Minimal dummy row
    dummy = pd.DataFrame([{
        "rainfall_1h": 45.0, "rainfall_3h": 110.0,
        "rainfall_6h": 180.0, "rainfall_24h": 200.0,
        "temperature": 21.0, "humidity": 85.0,
        "traffic_level": 0.65, "average_speed": 32.0,
        "road_condition": 0.40, "road_age": 12.0,
        "maintenance_score": 0.55,
        "slope": 22.0, "elevation": 850.0, "river_distance": 1.2,
        "historical_incidents": 5, "incident_count_7d": 2,
        "incident_count_30d": 6, "previous_disruptions": 3,
    }])

    result = engineer_features(dummy)
    print(f"  Input shape  : {dummy.shape}")
    print(f"  Output shape : {result.shape}")
    print(f"  Features     : {list(result.columns)}")
    print(f"\n  Sample values:")
    for col in result.columns:
        print(f"    {col:30s} = {result[col].values[0]:.4f}")
    print("\n✅ Feature engineering OK")
