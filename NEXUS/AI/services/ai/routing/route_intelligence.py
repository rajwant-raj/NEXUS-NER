"""
NEXUS-NER | Module H — Route Intelligence Engine
=================================================
Evaluates multiple route alternatives and returns the fastest, safest,
and balanced options with per-route risk scores.

The ML team owns the risk intelligence layer.
The GIS/routing team owns the geographic graph.
This module provides the risk-weighted route evaluation contract.

Route graph
-----------
For the prototype, route data is a static definition of corridors
connecting key Northeast India logistics hubs.  Replace this with a
live GIS graph in production.

Usage
-----
    from routing.route_intelligence import evaluate_routes

    result = evaluate_routes(
        origin="Guwahati",
        destination="Tawang",
        cargo_type="medical",
        priority="emergency",
    )
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Any

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))


# ---------------------------------------------------------------------------
# Static route graph (prototype)
# ---------------------------------------------------------------------------
# Each route entry defines:
#   segments      – list of road segment IDs along the route
#   distance_km   – total route distance
#   base_time_min – estimated travel time under normal conditions (minutes)
#   description   – human-readable route description

ROUTE_GRAPH: dict[tuple[str, str], list[dict]] = {
    ("Guwahati", "Tawang"): [
        {
            "route_id":       "route_a",
            "label":          "Route A — NH-15 Direct",
            "description":    "Via Bhalukpong, Bomdila. Fastest but exposed to landslides.",
            "segments":       ["NH15_001", "NH15_002", "NH15_003", "NH15_004", "NH15_005"],
            "distance_km":    445,
            "base_time_min":  482,   # 8h 02m
        },
        {
            "route_id":       "route_b",
            "label":          "Route B — NH-15 via Dirang",
            "description":    "Via Bhalukpong, Dirang, Sela Pass. Balanced option.",
            "segments":       ["NH15_001", "NH15_002", "NH27_001", "NH27_002", "NH27_003"],
            "distance_km":    478,
            "base_time_min":  519,   # 8h 39m
        },
        {
            "route_c":        "route_c",
            "route_id":       "route_c",
            "label":          "Route C — NH-13 via Ziro",
            "description":    "Via Ziro, Daporijo. Longest but avoids high-risk zones.",
            "segments":       ["NH13_001", "NH13_002", "NH13_003", "NH13_004", "NH13_005"],
            "distance_km":    561,
            "base_time_min":  558,   # 9h 18m
        },
    ],
    ("Guwahati", "Aizawl"): [
        {
            "route_id":       "route_a",
            "label":          "Route A — NH-306 Direct",
            "description":    "Most direct highway connection.",
            "segments":       ["NH37_001", "NH37_002"],
            "distance_km":    285,
            "base_time_min":  310,
        },
        {
            "route_id":       "route_b",
            "label":          "Route B — Via Silchar",
            "description":    "Via Silchar junction — moderate detour.",
            "segments":       ["NH37_001", "NH37_003", "NH37_004"],
            "distance_km":    340,
            "base_time_min":  375,
        },
    ],
    ("Guwahati", "Itanagar"): [
        {
            "route_id":       "route_a",
            "label":          "Route A — NH-415 Direct",
            "description":    "Direct national highway.",
            "segments":       ["NH27_001", "NH27_002"],
            "distance_km":    185,
            "base_time_min":  210,
        },
        {
            "route_id":       "route_b",
            "label":          "Route B — Via Naharlagun",
            "description":    "Alternate approach via Naharlagun.",
            "segments":       ["NH27_001", "SH01_001"],
            "distance_km":    195,
            "base_time_min":  230,
        },
    ],
}


# ---------------------------------------------------------------------------
# Cargo priority → risk weight mapping
# ---------------------------------------------------------------------------

CARGO_RISK_WEIGHTS = {
    # (cargo_type, priority) → alpha value in balanced cost
    # balanced_cost = alpha × norm_time + (1-alpha) × risk
    ("medical",   "emergency"):  0.25,   # 75% weight on safety
    ("medical",   "standard"):   0.35,
    ("supplies",  "emergency"):  0.35,
    ("supplies",  "standard"):   0.50,
    ("general",   "emergency"):  0.40,
    ("general",   "standard"):   0.55,
    ("fuel",      "emergency"):  0.30,
    ("fuel",      "standard"):   0.50,
}

DEFAULT_ALPHA = 0.50


# ---------------------------------------------------------------------------
# Segment risk fetcher
# ---------------------------------------------------------------------------

def _get_segment_risk(segment_id: str) -> float:
    """
    Fetch risk score for a road segment.
    In production: query backend for live risk data.
    In prototype: use a deterministic formula based on segment ID.
    """
    try:
        from inference.predictor import predict
        from risk.risk_engine import compute_risk

        # Generate realistic but deterministic features from segment ID hash
        h = abs(hash(segment_id)) % 10000

        features = {
            "rainfall_1h":          (h % 80) + 5.0,
            "rainfall_3h":          (h % 180) + 15.0,
            "traffic_level":        ((h % 60) + 10) / 100,
            "road_condition":       ((h % 60) + 30) / 100,
            "slope":                (h % 35) + 3.0,
            "river_distance":       (h % 15) + 0.5,
            "historical_incidents": h % 8,
            "maintenance_score":    ((h % 50) + 30) / 100,
            "road_age":             (h % 20) + 3.0,
        }

        pred = predict(features)
        risk_result = compute_risk(
            ml_probability=pred["probability"],
            rainfall_1h=features["rainfall_1h"],
            rainfall_3h=features["rainfall_3h"],
            road_condition=features["road_condition"],
            traffic_level=features["traffic_level"],
            historical_incidents=features["historical_incidents"],
            slope=features["slope"],
            river_distance=features["river_distance"],
            maintenance_score=features["maintenance_score"],
            road_age=features["road_age"],
        )
        return risk_result["final_risk"]

    except Exception:
        # Deterministic fallback (no model loaded)
        h = abs(hash(segment_id)) % 10000
        return round((h % 70 + 10) / 100, 4)


def _compute_route_risk(segments: list[str]) -> float:
    """Aggregate segment-level risks into a single route risk score."""
    if not segments:
        return 0.0
    risks = [_get_segment_risk(s) for s in segments]
    # Use 80th-percentile risk (a few bad segments matter more than the average)
    risks.sort()
    idx = int(0.80 * len(risks))
    p80 = risks[min(idx, len(risks) - 1)]
    avg = sum(risks) / len(risks)
    return round(0.60 * p80 + 0.40 * avg, 4)


# ---------------------------------------------------------------------------
# Travel time adjustment
# ---------------------------------------------------------------------------

def _adjusted_time(base_time_min: int, risk: float) -> int:
    """
    Adjust travel time based on risk (higher risk → slower traffic).
    """
    # Risk adds 0–50% to base travel time
    penalty = 1.0 + 0.50 * risk
    return int(base_time_min * penalty)


# ---------------------------------------------------------------------------
# Balanced cost function
# ---------------------------------------------------------------------------

def _balanced_cost(norm_time: float, risk: float, alpha: float) -> float:
    return alpha * norm_time + (1 - alpha) * risk


# ---------------------------------------------------------------------------
# Route recommendation reason
# ---------------------------------------------------------------------------

def _make_recommendation_reason(
    recommended_id: str,
    routes: dict[str, dict],
    fastest_id: str,
    safest_id: str,
) -> str:
    rec = routes[recommended_id]
    fastest = routes[fastest_id]
    safest = routes[safest_id]

    time_diff = rec["eta_minutes"] - fastest["eta_minutes"]
    risk_diff  = fastest["risk"] - rec["risk"]

    if recommended_id == fastest_id:
        return (
            f"Fastest route with acceptable risk level ({rec['risk']:.0%}). "
            f"No significant time saving from alternatives."
        )
    elif recommended_id == safest_id:
        time_penalty = rec["eta_minutes"] - fastest["eta_minutes"]
        return (
            f"Safest available route ({rec['risk']:.0%} risk). "
            f"Recommended due to high disruption risk on faster alternatives. "
            f"Additional travel time: {time_penalty} minutes."
        )
    else:
        return (
            f"Significantly lower disruption risk ({risk_diff:.0%} reduction) "
            f"compared to the fastest route, with only {time_diff} minutes of "
            f"additional travel time. Optimal risk-time balance."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_routes(
    origin: str,
    destination: str,
    cargo_type: str = "general",
    priority: str = "standard",
) -> dict[str, Any]:
    """
    Evaluate all routes between origin and destination.

    Parameters
    ----------
    origin      : departure location
    destination : arrival location
    cargo_type  : "medical" | "supplies" | "general" | "fuel"
    priority    : "emergency" | "standard"

    Returns
    -------
    dict with keys:
        routes      – dict of route_id → {eta_minutes, risk, risk_level, label}
        fastest     – route_id of fastest route
        safest      – route_id of safest route
        balanced    – route_id of balanced route
        recommended – {route_id, reason}
        metadata    – {origin, destination, cargo_type, priority, n_routes}
    """
    # Normalise inputs
    origin_key = origin.strip().title()
    dest_key   = destination.strip().title()
    key        = (origin_key, dest_key)

    if key not in ROUTE_GRAPH:
        # Try reverse lookup
        rev_key = (dest_key, origin_key)
        if rev_key in ROUTE_GRAPH:
            key = rev_key
        else:
            raise ValueError(
                f"No routes found for {origin} → {destination}.\n"
                f"Available corridors: {[' → '.join(k) for k in ROUTE_GRAPH.keys()]}"
            )

    route_defs = ROUTE_GRAPH[key]
    alpha = CARGO_RISK_WEIGHTS.get((cargo_type.lower(), priority.lower()), DEFAULT_ALPHA)

    # Build route profiles
    route_profiles: dict[str, dict] = {}
    for rd in route_defs:
        rid  = rd["route_id"]
        segs = rd["segments"]
        risk = _compute_route_risk(segs)
        eta  = _adjusted_time(rd["base_time_min"], risk)

        from risk.risk_engine import _risk_level
        route_profiles[rid] = {
            "route_id":    rid,
            "label":       rd.get("label", rid),
            "description": rd.get("description", ""),
            "distance_km": rd.get("distance_km", 0),
            "eta_minutes": eta,
            "risk":        risk,
            "risk_level":  _risk_level(risk),
            "segments":    segs,
        }

    if not route_profiles:
        raise ValueError("No routes could be evaluated.")

    # Identify fastest / safest
    fastest_id = min(route_profiles, key=lambda r: route_profiles[r]["eta_minutes"])
    safest_id  = min(route_profiles, key=lambda r: route_profiles[r]["risk"])

    # Balanced: minimise combined cost
    times = [v["eta_minutes"] for v in route_profiles.values()]
    min_t, max_t = min(times), max(times)
    range_t = max_t - min_t or 1

    balanced_id = min(
        route_profiles,
        key=lambda r: _balanced_cost(
            (route_profiles[r]["eta_minutes"] - min_t) / range_t,
            route_profiles[r]["risk"],
            alpha,
        )
    )

    # Recommended — use balanced unless risk difference is negligible
    recommended_id = balanced_id
    balanced_risk  = route_profiles[balanced_id]["risk"]
    safest_risk    = route_profiles[safest_id]["risk"]

    # If balanced and safest have similar time but very different risk, prefer safest
    if (safest_risk < balanced_risk - 0.15 and
            route_profiles[safest_id]["eta_minutes"] - route_profiles[balanced_id]["eta_minutes"] < 30):
        recommended_id = safest_id

    reason = _make_recommendation_reason(
        recommended_id, route_profiles, fastest_id, safest_id
    )

    return {
        "routes":    route_profiles,
        "fastest":   fastest_id,
        "safest":    safest_id,
        "balanced":  balanced_id,
        "recommended": {
            "route_id": recommended_id,
            "reason":   reason,
        },
        "metadata": {
            "origin":      origin_key,
            "destination": dest_key,
            "cargo_type":  cargo_type,
            "priority":    priority,
            "alpha":       alpha,
            "n_routes":    len(route_profiles),
        },
    }


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🗺️  NEXUS-NER | Route Intelligence — Smoke Test")
    print("=" * 60)

    result = evaluate_routes(
        origin="Guwahati",
        destination="Tawang",
        cargo_type="medical",
        priority="emergency",
    )

    print(f"\n  Origin      : {result['metadata']['origin']}")
    print(f"  Destination : {result['metadata']['destination']}")
    print(f"  Cargo       : {result['metadata']['cargo_type']} / {result['metadata']['priority']}")
    print(f"  Risk alpha  : {result['metadata']['alpha']}")

    print("\n  Route Comparison:")
    print(f"  {'Route':10s}  {'ETA':10s}  {'Risk':8s}  {'Level':10s}")
    print("  " + "─" * 45)
    for rid, r in result["routes"].items():
        tag = ""
        if rid == result["fastest"]:   tag += " ⚡FAST"
        if rid == result["safest"]:    tag += " 🛡️SAFE"
        if rid == result["balanced"]:  tag += " ⚖️ BAL"
        h, m = divmod(r["eta_minutes"], 60)
        print(f"  {rid:10s}  {h}h {m:02d}m      {r['risk']:.1%}    {r['risk_level']:10s}{tag}")

    rec = result["recommended"]
    print(f"\n  ✅ Recommendation: {rec['route_id'].upper()}")
    print(f"     Reason: {rec['reason']}")

    print("\n✅ Route intelligence OK")
