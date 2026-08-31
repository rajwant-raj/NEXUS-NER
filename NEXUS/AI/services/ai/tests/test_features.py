"""
NEXUS-NER | Tests — Feature Engineering
"""

import sys
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

from features.feature_engineering import (
    engineer_features,
    build_feature_pipeline,
    FEATURE_COLUMNS,
    RAW_FEATURE_COLUMNS,
    RoadFeatureEngineer,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_row():
    """Minimal valid input with all RAW_FEATURE_COLUMNS."""
    return pd.DataFrame([{
        "rainfall_1h": 10.0, "rainfall_3h": 25.0,
        "rainfall_6h": 40.0, "rainfall_24h": 60.0,
        "temperature": 22.0, "humidity": 70.0,
        "traffic_level": 0.30, "average_speed": 45.0,
        "road_condition": 0.75, "road_age": 8.0,
        "maintenance_score": 0.70,
        "slope": 6.0, "elevation": 400.0, "river_distance": 5.0,
        "historical_incidents": 1, "incident_count_7d": 0,
        "incident_count_30d": 1, "previous_disruptions": 0,
    }])


@pytest.fixture
def batch_df():
    """10-row DataFrame for batch testing."""
    rng = np.random.default_rng(42)
    n = 10
    return pd.DataFrame({
        "rainfall_1h":          rng.uniform(0, 120, n),
        "rainfall_3h":          rng.uniform(0, 300, n),
        "rainfall_6h":          rng.uniform(0, 400, n),
        "rainfall_24h":         rng.uniform(0, 500, n),
        "temperature":          rng.uniform(10, 35, n),
        "humidity":             rng.uniform(40, 100, n),
        "traffic_level":        rng.uniform(0, 1, n),
        "average_speed":        rng.uniform(10, 80, n),
        "road_condition":       rng.uniform(0, 1, n),
        "road_age":             rng.uniform(1, 30, n),
        "maintenance_score":    rng.uniform(0, 1, n),
        "slope":                rng.uniform(0, 50, n),
        "elevation":            rng.uniform(100, 3000, n),
        "river_distance":       rng.uniform(0.1, 20, n),
        "historical_incidents": rng.integers(0, 15, n),
        "incident_count_7d":   rng.integers(0, 5, n),
        "incident_count_30d":  rng.integers(0, 12, n),
        "previous_disruptions": rng.integers(0, 8, n),
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFeatureEngineering:

    def test_output_shape_single_row(self, minimal_row):
        result = engineer_features(minimal_row)
        assert result.shape == (1, len(FEATURE_COLUMNS)), (
            f"Expected shape (1, {len(FEATURE_COLUMNS)}), got {result.shape}"
        )

    def test_output_shape_batch(self, batch_df):
        result = engineer_features(batch_df)
        assert result.shape == (10, len(FEATURE_COLUMNS))

    def test_no_nan_values(self, batch_df):
        result = engineer_features(batch_df)
        assert not result.isnull().any().any(), "Output contains NaN values"

    def test_column_names_correct(self, minimal_row):
        result = engineer_features(minimal_row)
        assert list(result.columns) == FEATURE_COLUMNS

    def test_rainfall_intensity_range(self, minimal_row):
        result = engineer_features(minimal_row)
        # rainfall_intensity = rainfall_1h / (rainfall_24h + 1)
        val = result["rainfall_intensity"].values[0]
        assert val >= 0, "rainfall_intensity must be non-negative"

    def test_terrain_risk_range(self, batch_df):
        result = engineer_features(batch_df)
        terrain = result["terrain_risk"]
        assert (terrain >= 0).all() and (terrain <= 1).all(), (
            "terrain_risk must be in [0, 1]"
        )

    def test_congestion_score_range(self, batch_df):
        result = engineer_features(batch_df)
        cong = result["congestion_score"]
        assert (cong >= 0).all() and (cong <= 1).all()

    def test_historical_risk_range(self, batch_df):
        result = engineer_features(batch_df)
        hr = result["historical_risk"]
        assert (hr >= 0).all() and (hr <= 1).all()

    def test_road_condition_score_range(self, batch_df):
        result = engineer_features(batch_df)
        rcs = result["road_condition_score"]
        assert (rcs >= 0).all() and (rcs <= 1).all()

    def test_pipeline_with_scaler(self, batch_df):
        pipeline = build_feature_pipeline(scale=True)
        arr = pipeline.fit_transform(batch_df)
        assert arr.shape == (10, len(FEATURE_COLUMNS))
        # Scaled output should have near-zero mean
        assert abs(arr.mean()) < 1.0

    def test_pipeline_without_scaler(self, batch_df):
        pipeline = build_feature_pipeline(scale=False)
        arr = pipeline.fit_transform(batch_df)
        assert arr.shape == (10, len(FEATURE_COLUMNS))

    def test_transformer_requires_dataframe(self):
        transformer = RoadFeatureEngineer()
        with pytest.raises(ValueError, match="pandas DataFrame"):
            transformer.transform(np.zeros((1, 18)))

    def test_high_rainfall_increases_intensity(self):
        low_rain_row  = pd.DataFrame([{"rainfall_1h": 5,  **_base_row()}])
        high_rain_row = pd.DataFrame([{"rainfall_1h": 100, **_base_row()}])

        low  = engineer_features(low_rain_row)["rainfall_intensity"].values[0]
        high = engineer_features(high_rain_row)["rainfall_intensity"].values[0]
        assert high > low, "Higher rainfall_1h should give higher rainfall_intensity"

    def test_poor_road_reduces_road_condition_score(self):
        good_row = pd.DataFrame([{"road_condition": 0.95, "maintenance_score": 0.90, **_base_row_no_road()}])
        poor_row = pd.DataFrame([{"road_condition": 0.15, "maintenance_score": 0.20, **_base_row_no_road()}])

        good = engineer_features(good_row)["road_condition_score"].values[0]
        poor = engineer_features(poor_row)["road_condition_score"].values[0]
        assert good > poor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_row():
    return {
        "rainfall_3h": 20, "rainfall_6h": 30, "rainfall_24h": 50,
        "temperature": 22, "humidity": 70,
        "traffic_level": 0.30, "average_speed": 45,
        "road_condition": 0.75, "road_age": 8, "maintenance_score": 0.70,
        "slope": 6, "elevation": 400, "river_distance": 5,
        "historical_incidents": 1, "incident_count_7d": 0,
        "incident_count_30d": 1, "previous_disruptions": 0,
    }


def _base_row_no_road():
    return {
        "rainfall_1h": 10, "rainfall_3h": 20, "rainfall_6h": 30, "rainfall_24h": 50,
        "temperature": 22, "humidity": 70,
        "traffic_level": 0.30, "average_speed": 45,
        "road_age": 8,
        "slope": 6, "elevation": 400, "river_distance": 5,
        "historical_incidents": 1, "incident_count_7d": 0,
        "incident_count_30d": 1, "previous_disruptions": 0,
    }
