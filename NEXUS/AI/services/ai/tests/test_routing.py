"""
NEXUS-NER | Tests — Routing
"""

import sys
import pytest
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

from routing.route_intelligence import evaluate_routes, ROUTE_GRAPH


class TestRouteIntelligence:

    def test_valid_corridor_returns_result(self):
        result = evaluate_routes("Guwahati", "Tawang")
        assert "routes" in result
        assert "fastest" in result
        assert "safest" in result
        assert "balanced" in result
        assert "recommended" in result

    def test_routes_not_empty(self):
        result = evaluate_routes("Guwahati", "Tawang")
        assert len(result["routes"]) >= 2

    def test_route_ids_are_valid(self):
        result = evaluate_routes("Guwahati", "Tawang")
        route_ids = set(result["routes"].keys())
        assert result["fastest"]  in route_ids
        assert result["safest"]   in route_ids
        assert result["balanced"] in route_ids

    def test_recommended_is_valid_route(self):
        result = evaluate_routes("Guwahati", "Tawang")
        rec_id = result["recommended"]["route_id"]
        assert rec_id in result["routes"]

    def test_recommended_has_reason(self):
        result = evaluate_routes("Guwahati", "Tawang")
        assert len(result["recommended"]["reason"]) > 10

    def test_risk_values_in_range(self):
        result = evaluate_routes("Guwahati", "Tawang")
        for rid, r in result["routes"].items():
            assert 0.0 <= r["risk"] <= 1.0, f"Risk out of range for {rid}: {r['risk']}"

    def test_risk_level_valid(self):
        result = evaluate_routes("Guwahati", "Tawang")
        valid_levels = {"SAFE", "MODERATE", "HIGH", "CRITICAL"}
        for rid, r in result["routes"].items():
            assert r["risk_level"] in valid_levels

    def test_eta_minutes_positive(self):
        result = evaluate_routes("Guwahati", "Tawang")
        for rid, r in result["routes"].items():
            assert r["eta_minutes"] > 0

    def test_safest_has_lowest_risk(self):
        result = evaluate_routes("Guwahati", "Tawang")
        safest_risk = result["routes"][result["safest"]]["risk"]
        for rid, r in result["routes"].items():
            assert safest_risk <= r["risk"] + 1e-6, (
                f"Safest route ({result['safest']}) has higher risk than {rid}"
            )

    def test_fastest_has_lowest_eta(self):
        result = evaluate_routes("Guwahati", "Tawang")
        fastest_eta = result["routes"][result["fastest"]]["eta_minutes"]
        for rid, r in result["routes"].items():
            assert fastest_eta <= r["eta_minutes"] + 1, (
                f"Fastest route has higher ETA than {rid}"
            )

    def test_emergency_cargo_uses_stricter_alpha(self):
        standard  = evaluate_routes("Guwahati", "Tawang", cargo_type="general",  priority="standard")
        emergency = evaluate_routes("Guwahati", "Tawang", cargo_type="medical",  priority="emergency")
        # Emergency should have lower alpha (more weight on safety)
        assert emergency["metadata"]["alpha"] < standard["metadata"]["alpha"]

    def test_unknown_corridor_raises(self):
        with pytest.raises(ValueError, match="No routes found"):
            evaluate_routes("Mars", "Jupiter")

    def test_metadata_contains_expected_keys(self):
        result = evaluate_routes("Guwahati", "Tawang")
        for key in ("origin", "destination", "cargo_type", "priority", "n_routes"):
            assert key in result["metadata"], f"Missing metadata key: {key}"

    def test_all_defined_corridors_work(self):
        for (origin, dest) in ROUTE_GRAPH.keys():
            result = evaluate_routes(origin, dest)
            assert len(result["routes"]) > 0
