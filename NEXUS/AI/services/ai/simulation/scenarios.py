"""
NEXUS-NER | Module G — What-If Scenario Simulator
==================================================
Pre-built scenarios that stress-test the AI pipeline under different
environmental conditions.  Designed for the SIH live demonstration.

Scenarios
---------
    NORMAL            – Clear day, good road, low traffic
    HEAVY_RAIN        – 90 mm/h rainfall
    EXTREME_RAIN      – 150 mm/h rainfall
    HIGH_TRAFFIC      – Peak-hour congestion
    POOR_ROAD         – Damaged road surface
    LANDSLIDE         – Extreme rain + poor road + steep slope
    COMBINED          – Heavy rain + poor road + high traffic (worst case)

Usage
-----
    from simulation.scenarios import run_scenario, run_all_scenarios

    result = run_scenario("HEAVY_RAIN")
    all_results = run_all_scenarios()
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIO_DEFINITIONS: dict[str, dict[str, Any]] = {
    "NORMAL": {
        "description": "Clear day — normal operating conditions",
        "rainfall_1h": 5.0,
        "rainfall_3h": 10.0,
        "rainfall_6h": 15.0,
        "rainfall_24h": 20.0,
        "temperature": 23.0,
        "humidity": 60.0,
        "traffic_level": 0.20,
        "average_speed": 55.0,
        "road_condition": 0.85,
        "road_age": 8.0,
        "maintenance_score": 0.78,
        "slope": 6.0,
        "elevation": 400.0,
        "river_distance": 7.0,
        "historical_incidents": 1,
        "incident_count_7d": 0,
        "incident_count_30d": 1,
        "previous_disruptions": 0,
    },
    "HEAVY_RAIN": {
        "description": "Heavy monsoon rainfall — road surfaces stressed",
        "rainfall_1h": 90.0,
        "rainfall_3h": 210.0,
        "rainfall_6h": 290.0,
        "rainfall_24h": 350.0,
        "temperature": 18.0,
        "humidity": 92.0,
        "traffic_level": 0.25,
        "average_speed": 40.0,
        "road_condition": 0.80,
        "road_age": 8.0,
        "maintenance_score": 0.75,
        "slope": 6.0,
        "elevation": 400.0,
        "river_distance": 7.0,
        "historical_incidents": 1,
        "incident_count_7d": 0,
        "incident_count_30d": 1,
        "previous_disruptions": 0,
    },
    "EXTREME_RAIN": {
        "description": "Extreme rainfall event — flash flood conditions likely",
        "rainfall_1h": 150.0,
        "rainfall_3h": 380.0,
        "rainfall_6h": 500.0,
        "rainfall_24h": 650.0,
        "temperature": 16.0,
        "humidity": 98.0,
        "traffic_level": 0.15,
        "average_speed": 25.0,
        "road_condition": 0.70,
        "road_age": 8.0,
        "maintenance_score": 0.72,
        "slope": 8.0,
        "elevation": 550.0,
        "river_distance": 4.0,
        "historical_incidents": 2,
        "incident_count_7d": 1,
        "incident_count_30d": 2,
        "previous_disruptions": 1,
    },
    "HIGH_TRAFFIC": {
        "description": "Peak-hour congestion — logistics delays likely",
        "rainfall_1h": 5.0,
        "rainfall_3h": 10.0,
        "rainfall_6h": 15.0,
        "rainfall_24h": 20.0,
        "temperature": 24.0,
        "humidity": 55.0,
        "traffic_level": 0.92,
        "average_speed": 12.0,
        "road_condition": 0.82,
        "road_age": 10.0,
        "maintenance_score": 0.70,
        "slope": 4.0,
        "elevation": 300.0,
        "river_distance": 6.0,
        "historical_incidents": 3,
        "incident_count_7d": 1,
        "incident_count_30d": 4,
        "previous_disruptions": 1,
    },
    "POOR_ROAD": {
        "description": "Severely degraded road surface — structural risk",
        "rainfall_1h": 8.0,
        "rainfall_3h": 20.0,
        "rainfall_6h": 28.0,
        "rainfall_24h": 35.0,
        "temperature": 25.0,
        "humidity": 65.0,
        "traffic_level": 0.35,
        "average_speed": 28.0,
        "road_condition": 0.20,
        "road_age": 25.0,
        "maintenance_score": 0.18,
        "slope": 10.0,
        "elevation": 600.0,
        "river_distance": 3.0,
        "historical_incidents": 8,
        "incident_count_7d": 2,
        "incident_count_30d": 7,
        "previous_disruptions": 4,
    },
    "LANDSLIDE": {
        "description": "Landslide-risk conditions — extreme rain, steep terrain, poor road",
        "rainfall_1h": 120.0,
        "rainfall_3h": 310.0,
        "rainfall_6h": 420.0,
        "rainfall_24h": 580.0,
        "temperature": 14.0,
        "humidity": 97.0,
        "traffic_level": 0.10,
        "average_speed": 18.0,
        "road_condition": 0.15,
        "road_age": 22.0,
        "maintenance_score": 0.20,
        "slope": 42.0,
        "elevation": 1800.0,
        "river_distance": 0.5,
        "historical_incidents": 12,
        "incident_count_7d": 4,
        "incident_count_30d": 11,
        "previous_disruptions": 7,
    },
    "COMBINED": {
        "description": "Combined disruption — heavy rain + poor road + high traffic",
        "rainfall_1h": 90.0,
        "rainfall_3h": 210.0,
        "rainfall_6h": 290.0,
        "rainfall_24h": 380.0,
        "temperature": 17.0,
        "humidity": 94.0,
        "traffic_level": 0.80,
        "average_speed": 15.0,
        "road_condition": 0.30,
        "road_age": 18.0,
        "maintenance_score": 0.35,
        "slope": 18.0,
        "elevation": 900.0,
        "river_distance": 0.9,
        "historical_incidents": 7,
        "incident_count_7d": 3,
        "incident_count_30d": 9,
        "previous_disruptions": 4,
    },
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_scenario(name: str, road_id: str = "NH13_042") -> dict[str, Any]:
    """
    Run a named scenario through the full AI pipeline.

    Parameters
    ----------
    name    : scenario name (see SCENARIO_DEFINITIONS)
    road_id : road identifier to include in output

    Returns
    -------
    dict with full pipeline output
    """
    name = name.upper()
    if name not in SCENARIO_DEFINITIONS:
        valid = list(SCENARIO_DEFINITIONS.keys())
        raise ValueError(f"Unknown scenario '{name}'. Valid: {valid}")

    scenario = SCENARIO_DEFINITIONS[name].copy()
    description = scenario.pop("description")

    # Import here to avoid circular imports at module level
    try:
        from inference.predictor import predict
        from risk.risk_engine import compute_risk
        from explainability.explainer import explain

        pred = predict(scenario)
        ml_prob = pred["probability"]

        risk_result = compute_risk(
            ml_probability=ml_prob,
            rainfall_1h=scenario["rainfall_1h"],
            rainfall_3h=scenario["rainfall_3h"],
            rainfall_24h=scenario.get("rainfall_24h", 0),
            humidity=scenario.get("humidity", 70),
            temperature=scenario.get("temperature", 22),
            road_condition=scenario["road_condition"],
            maintenance_score=scenario.get("maintenance_score", 0.7),
            road_age=scenario.get("road_age", 10),
            traffic_level=scenario["traffic_level"],
            average_speed=scenario.get("average_speed", 40),
            historical_incidents=scenario["historical_incidents"],
            incident_count_7d=scenario.get("incident_count_7d", 0),
            incident_count_30d=scenario.get("incident_count_30d", 0),
            previous_disruptions=scenario.get("previous_disruptions", 0),
            slope=scenario["slope"],
            river_distance=scenario["river_distance"],
            elevation=scenario.get("elevation", 500),
        )

        expl = explain(scenario, ml_probability=ml_prob)

    except FileNotFoundError:
        # Model not trained yet — use heuristic
        from explainability.explainer import _heuristic_explain
        ml_prob = _compute_heuristic_probability(scenario)
        risk_result = {
            "final_risk": ml_prob,
            "risk_level": _heuristic_risk_level(ml_prob),
            "components": {},
        }
        expl = _heuristic_explain(scenario, ml_prob, top_n=5)

    return {
        "scenario":    name,
        "description": description,
        "road_id":     road_id,
        "inputs": {
            "rainfall_1h":    scenario["rainfall_1h"],
            "rainfall_3h":    scenario.get("rainfall_3h"),
            "road_condition": scenario["road_condition"],
            "traffic_level":  scenario["traffic_level"],
            "slope":          scenario["slope"],
        },
        "ml_probability":  ml_prob,
        "final_risk":      risk_result["final_risk"],
        "risk_level":      risk_result["risk_level"],
        "factors":         expl["factors"],
        "risk_components": risk_result.get("components", {}),
    }


def run_all_scenarios(road_id: str = "NH13_042") -> list[dict[str, Any]]:
    """Run all pre-defined scenarios and return a list of results."""
    results = []
    for name in SCENARIO_DEFINITIONS:
        try:
            r = run_scenario(name, road_id=road_id)
            results.append(r)
        except Exception as e:
            results.append({"scenario": name, "error": str(e)})
    return results


# ---------------------------------------------------------------------------
# Heuristic fallback (when model is not yet trained)
# ---------------------------------------------------------------------------

def _compute_heuristic_probability(s: dict) -> float:
    import math
    rain = math.tanh(s.get("rainfall_1h", 0) / 60)
    road = 1 - s.get("road_condition", 1)
    slope = math.tanh(s.get("slope", 0) / 30)
    traffic = s.get("traffic_level", 0) * 0.3
    hist = math.tanh(s.get("historical_incidents", 0) / 8)
    river = math.exp(-s.get("river_distance", 10) / 2)
    raw = 0.35 * rain + 0.25 * road + 0.15 * slope + 0.10 * traffic + 0.10 * hist + 0.05 * river
    return round(min(max(raw, 0.0), 1.0), 4)


def _heuristic_risk_level(p: float) -> str:
    if p < 0.25:
        return "SAFE"
    elif p < 0.50:
        return "MODERATE"
    elif p < 0.75:
        return "HIGH"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🎭 NEXUS-NER | What-If Scenario Simulator")
    print("=" * 60)

    results = run_all_scenarios()
    for r in results:
        if "error" in r:
            print(f"\n  ❌ {r['scenario']}: {r['error']}")
            continue

        bar = "█" * int(r["final_risk"] * 30)
        print(f"\n  [{r['scenario']:20s}]  {r['final_risk']:.1%}  {r['risk_level']:8s}  {bar}")
        print(f"     Rainfall  : {r['inputs']['rainfall_1h']:6.1f} mm/h   "
              f"Road cond: {r['inputs']['road_condition']:.2f}")
        if r["factors"]:
            print(f"     Factors   : {', '.join(r['factors'][:3])}")

    print("\n✅ Scenario simulation complete")
