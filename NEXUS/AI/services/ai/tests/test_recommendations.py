"""
NEXUS-NER | Tests — Recommendation / Decision Engine
"""

import sys
import pytest
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

from recommendations.decision_engine import (
    recommend_action,
    recommend_route_action,
    STANDARD_THRESHOLDS,
    EMERGENCY_THRESHOLDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_ROUTE_EVAL = {
    "routes": {
        "route_a": {"label": "Route A", "eta_minutes": 482, "risk": 0.78, "risk_level": "CRITICAL"},
        "route_b": {"label": "Route B", "eta_minutes": 519, "risk": 0.21, "risk_level": "SAFE"},
        "route_c": {"label": "Route C", "eta_minutes": 558, "risk": 0.17, "risk_level": "SAFE"},
    },
    "fastest":  "route_a",
    "safest":   "route_c",
    "balanced": "route_b",
    "recommended": {"route_id": "route_b", "reason": "Best risk-time balance."},
}

LOW_RISK_ROUTE_EVAL = {
    "routes": {
        "route_a": {"label": "Route A", "eta_minutes": 300, "risk": 0.12, "risk_level": "SAFE"},
        "route_b": {"label": "Route B", "eta_minutes": 340, "risk": 0.10, "risk_level": "SAFE"},
    },
    "fastest":  "route_a",
    "safest":   "route_b",
    "balanced": "route_a",
    "recommended": {"route_id": "route_a", "reason": "Low risk, fast route."},
}


# ---------------------------------------------------------------------------
# Tests — recommend_action (single road)
# ---------------------------------------------------------------------------

class TestRecommendAction:

    def test_output_keys(self):
        result = recommend_action(risk_score=0.50, risk_level="HIGH")
        for key in ("action", "priority", "road_id", "risk_score", "risk_level", "reason", "factors"):
            assert key in result

    def test_valid_action_values(self):
        valid = {"MONITOR", "WARN", "REROUTE", "BLOCK_ROUTE", "ESCALATE"}
        for score in [0.10, 0.35, 0.65, 0.90]:
            result = recommend_action(risk_score=score, risk_level="HIGH")
            assert result["action"] in valid

    def test_valid_priority_values(self):
        valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for score in [0.10, 0.35, 0.65, 0.90]:
            result = recommend_action(risk_score=score, risk_level="HIGH")
            assert result["priority"] in valid

    def test_low_risk_is_monitor(self):
        result = recommend_action(risk_score=0.10, risk_level="SAFE")
        assert result["action"] == "MONITOR"
        assert result["priority"] == "LOW"

    def test_high_risk_is_reroute_or_block(self):
        result = recommend_action(risk_score=0.72, risk_level="HIGH")
        assert result["action"] in ("REROUTE", "BLOCK_ROUTE")

    def test_critical_risk_is_block(self):
        result = recommend_action(risk_score=0.90, risk_level="CRITICAL")
        assert result["action"] in ("BLOCK_ROUTE", "ESCALATE")

    def test_emergency_medical_uses_stricter_thresholds(self):
        # At 0.45, standard → WARN, emergency medical → REROUTE
        standard  = recommend_action(risk_score=0.45, risk_level="MODERATE",
                                     cargo_type="general", priority="standard")
        emergency = recommend_action(risk_score=0.45, risk_level="MODERATE",
                                     cargo_type="medical", priority="emergency")

        # Emergency should have equal or stricter action
        action_rank = {"MONITOR": 0, "WARN": 1, "REROUTE": 2, "BLOCK_ROUTE": 3, "ESCALATE": 4}
        assert action_rank[emergency["action"]] >= action_rank[standard["action"]]

    def test_emergency_block_becomes_escalate(self):
        result = recommend_action(
            risk_score=0.90, risk_level="CRITICAL",
            cargo_type="medical", priority="emergency",
        )
        assert result["action"] == "ESCALATE"

    def test_road_id_preserved(self):
        result = recommend_action(risk_score=0.30, risk_level="MODERATE", road_id="NH13_042")
        assert result["road_id"] == "NH13_042"

    def test_factors_preserved(self):
        factors = ["Heavy rainfall", "Poor road condition"]
        result = recommend_action(risk_score=0.70, risk_level="HIGH", factors=factors)
        assert result["factors"] == factors

    def test_reason_is_non_empty(self):
        result = recommend_action(risk_score=0.50, risk_level="HIGH")
        assert len(result["reason"]) > 0

    def test_thresholds_applied_field(self):
        std = recommend_action(risk_score=0.50, risk_level="HIGH",
                                cargo_type="general", priority="standard")
        eme = recommend_action(risk_score=0.50, risk_level="HIGH",
                                cargo_type="medical", priority="emergency")
        assert std["thresholds_applied"] == "standard"
        assert eme["thresholds_applied"] == "emergency"

    def test_risk_score_preserved(self):
        result = recommend_action(risk_score=0.68, risk_level="HIGH")
        assert abs(result["risk_score"] - 0.68) < 0.01


# ---------------------------------------------------------------------------
# Tests — recommend_route_action
# ---------------------------------------------------------------------------

class TestRecommendRouteAction:

    def test_output_keys(self):
        result = recommend_route_action(MOCK_ROUTE_EVAL)
        for key in ("action", "priority", "recommended_route", "reason", "route_comparison"):
            assert key in result

    def test_valid_action_for_high_risk_route(self):
        result = recommend_route_action(MOCK_ROUTE_EVAL, cargo_type="general", priority="standard")
        assert result["action"] in ("REROUTE", "BLOCK_ROUTE", "ESCALATE")

    def test_monitor_for_low_risk_routes(self):
        result = recommend_route_action(LOW_RISK_ROUTE_EVAL)
        assert result["action"] == "MONITOR"

    def test_recommended_route_is_valid(self):
        result = recommend_route_action(MOCK_ROUTE_EVAL)
        assert result["recommended_route"] in MOCK_ROUTE_EVAL["routes"]

    def test_route_comparison_contains_all_routes(self):
        result = recommend_route_action(MOCK_ROUTE_EVAL)
        for rid in MOCK_ROUTE_EVAL["routes"]:
            assert rid in result["route_comparison"]

    def test_emergency_cargo_raises_priority(self):
        std = recommend_route_action(MOCK_ROUTE_EVAL, cargo_type="general",  priority="standard")
        eme = recommend_route_action(MOCK_ROUTE_EVAL, cargo_type="medical",  priority="emergency")
        rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        assert rank[eme["priority"]] >= rank[std["priority"]]

    def test_empty_routes_returns_monitor(self):
        result = recommend_route_action({"routes": {}, "fastest": None, "safest": None,
                                          "balanced": None, "recommended": {}})
        assert result["action"] == "MONITOR"
