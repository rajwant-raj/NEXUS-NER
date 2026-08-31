"""
NEXUS-NER | Tests — Risk Engine
"""

import sys
import pytest
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

from risk.risk_engine import compute_risk, WEIGHTS


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

BASE_KWARGS = dict(
    ml_probability=0.50,
    rainfall_1h=30.0,
    rainfall_3h=80.0,
    road_condition=0.65,
    traffic_level=0.40,
    historical_incidents=2,
    slope=10.0,
    river_distance=4.0,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRiskEngine:

    # ── Output contract ──────────────────────────────────────────────────────

    def test_output_keys(self):
        result = compute_risk(**BASE_KWARGS)
        assert "final_risk" in result
        assert "risk_level" in result
        assert "components" in result

    def test_final_risk_in_range(self):
        result = compute_risk(**BASE_KWARGS)
        assert 0.0 <= result["final_risk"] <= 1.0

    def test_risk_level_valid(self):
        result = compute_risk(**BASE_KWARGS)
        assert result["risk_level"] in ("SAFE", "MODERATE", "HIGH", "CRITICAL")

    def test_components_keys_match_weights(self):
        result = compute_risk(**BASE_KWARGS)
        for key in WEIGHTS:
            assert key in result["components"], f"Missing component: {key}"

    def test_components_all_in_range(self):
        result = compute_risk(**BASE_KWARGS)
        for key, val in result["components"].items():
            assert 0.0 <= val <= 1.0, f"Component {key} = {val} out of [0,1]"

    # ── Risk category thresholds ─────────────────────────────────────────────

    def test_safe_category(self):
        result = compute_risk(
            ml_probability=0.05, rainfall_1h=2, rainfall_3h=5,
            road_condition=0.95, traffic_level=0.05,
            historical_incidents=0, slope=1.0, river_distance=15.0,
            maintenance_score=0.95, humidity=40,
        )
        assert result["risk_level"] == "SAFE"
        assert result["final_risk"] < 0.25

    def test_critical_category(self):
        result = compute_risk(
            ml_probability=0.97, rainfall_1h=150, rainfall_3h=380,
            road_condition=0.10, traffic_level=0.90,
            historical_incidents=15, slope=45.0, river_distance=0.2,
            maintenance_score=0.05, humidity=99,
        )
        assert result["risk_level"] == "CRITICAL"
        assert result["final_risk"] >= 0.75

    # ── Monotonicity ──────────────────────────────────────────────────────────

    def test_higher_ml_probability_increases_risk(self):
        low  = compute_risk(ml_probability=0.10, **{k: v for k, v in BASE_KWARGS.items() if k != "ml_probability"})
        high = compute_risk(ml_probability=0.90, **{k: v for k, v in BASE_KWARGS.items() if k != "ml_probability"})
        assert high["final_risk"] > low["final_risk"]

    def test_heavier_rain_increases_risk(self):
        dry  = compute_risk(**{**BASE_KWARGS, "rainfall_1h": 2,   "rainfall_3h": 5})
        rain = compute_risk(**{**BASE_KWARGS, "rainfall_1h": 120, "rainfall_3h": 300})
        assert rain["final_risk"] > dry["final_risk"]

    def test_poor_road_increases_risk(self):
        good = compute_risk(**{**BASE_KWARGS, "road_condition": 0.95})
        poor = compute_risk(**{**BASE_KWARGS, "road_condition": 0.10})
        assert poor["final_risk"] > good["final_risk"]

    def test_steep_slope_increases_risk(self):
        flat  = compute_risk(**{**BASE_KWARGS, "slope": 1.0})
        steep = compute_risk(**{**BASE_KWARGS, "slope": 50.0})
        assert steep["final_risk"] > flat["final_risk"]

    def test_close_river_increases_risk(self):
        far   = compute_risk(**{**BASE_KWARGS, "river_distance": 18.0})
        close = compute_risk(**{**BASE_KWARGS, "river_distance": 0.2})
        assert close["final_risk"] > far["final_risk"]

    def test_more_history_increases_risk(self):
        clean = compute_risk(**{**BASE_KWARGS, "historical_incidents": 0})
        heavy = compute_risk(**{**BASE_KWARGS, "historical_incidents": 20})
        assert heavy["final_risk"] > clean["final_risk"]

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_all_zero_inputs(self):
        result = compute_risk(
            ml_probability=0.0, rainfall_1h=0, rainfall_3h=0,
            road_condition=1.0, traffic_level=0.0,
            historical_incidents=0, slope=0.0, river_distance=20.0,
        )
        assert 0.0 <= result["final_risk"] <= 1.0

    def test_all_max_inputs(self):
        result = compute_risk(
            ml_probability=1.0, rainfall_1h=500, rainfall_3h=1000,
            road_condition=0.0, traffic_level=1.0,
            historical_incidents=100, slope=90.0, river_distance=0.0,
            rainfall_24h=3000, humidity=100,
        )
        assert 0.0 <= result["final_risk"] <= 1.0

    def test_ml_probability_clamped(self):
        # Should not raise even with out-of-range ml_probability
        result = compute_risk(
            ml_probability=1.5,   # above 1.0
            **{k: v for k, v in BASE_KWARGS.items() if k != "ml_probability"},
        )
        assert result["components"]["ml_probability"] == 1.0

    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9
