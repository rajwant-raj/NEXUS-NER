"""
NEXUS-NER | Module I — Decision & Recommendation Engine
========================================================
Converts model predictions and route evaluation into a concrete,
actionable recommendation with priority and human-readable reasoning.

Possible actions
----------------
    MONITOR         – Risk is low, continue normal operations
    WARN            – Risk is elevated, dispatch should be cautious
    REROUTE         – Risk exceeds safe threshold, use alternate route
    BLOCK_ROUTE     – Route is critically dangerous, block dispatches
    ESCALATE        – Situation requires human intervention

Usage
-----
    from recommendations.decision_engine import recommend_action
    from recommendations.decision_engine import recommend_route_action

    # Single-road prediction decision
    action = recommend_action(
        road_id="NH13_042",
        risk_score=0.68,
        risk_level="HIGH",
        factors=["Heavy rainfall", "Poor road condition"],
    )

    # Route-level decision
    action = recommend_route_action(
        route_evaluation=evaluate_routes(...),
        cargo_type="medical",
        priority="emergency",
    )
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Standard cargo thresholds
STANDARD_THRESHOLDS = {
    "monitor":  (0.00, 0.30),
    "warn":     (0.30, 0.55),
    "reroute":  (0.55, 0.78),
    "block":    (0.78, 1.01),
}

# Emergency / medical cargo — stricter (lower thresholds)
EMERGENCY_THRESHOLDS = {
    "monitor":  (0.00, 0.20),
    "warn":     (0.20, 0.40),
    "reroute":  (0.40, 0.65),
    "block":    (0.65, 1.01),
}

PRIORITY_LEVELS = {
    "monitor": "LOW",
    "warn":    "MEDIUM",
    "reroute": "HIGH",
    "block":   "CRITICAL",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_thresholds(cargo_type: str, priority: str) -> dict[str, tuple]:
    if priority.lower() == "emergency" or cargo_type.lower() in ("medical",):
        return EMERGENCY_THRESHOLDS
    return STANDARD_THRESHOLDS


def _classify_action(risk_score: float, thresholds: dict) -> str:
    for action, (lo, hi) in thresholds.items():
        if lo <= risk_score < hi:
            return action
    return "block"


def _format_reason(
    action: str,
    risk_score: float,
    risk_level: str,
    factors: list[str],
    road_id: str = "",
) -> str:
    factor_summary = ""
    if factors:
        factor_summary = " Key factors: " + "; ".join(factors[:3]) + "."

    prefix = f"Road {road_id} — " if road_id else ""

    messages = {
        "monitor": (
            f"{prefix}Risk level is {risk_level} ({risk_score:.0%}). "
            "Normal operations. Continue monitoring.{factor_summary}"
        ),
        "warn": (
            f"{prefix}Elevated disruption risk detected ({risk_score:.0%} — {risk_level}). "
            f"Dispatch should exercise caution.{factor_summary}"
        ),
        "reroute": (
            f"{prefix}Road disruption probability exceeded safe threshold "
            f"({risk_score:.0%} — {risk_level}). Alternate route recommended.{factor_summary}"
        ),
        "block": (
            f"{prefix}CRITICAL disruption risk ({risk_score:.0%}). "
            f"Route is not safe for dispatch.{factor_summary}"
        ),
    }
    return messages.get(action, "Unknown action.").format(factor_summary=factor_summary)


# ---------------------------------------------------------------------------
# Single-road action
# ---------------------------------------------------------------------------

def recommend_action(
    risk_score: float,
    risk_level: str,
    road_id: str = "",
    factors: list[str] | None = None,
    cargo_type: str = "general",
    priority: str = "standard",
) -> dict[str, Any]:
    """
    Recommend an action for a single road segment.

    Parameters
    ----------
    risk_score   : float in [0, 1] — final composite risk score
    risk_level   : "SAFE" | "MODERATE" | "HIGH" | "CRITICAL"
    road_id      : road segment identifier
    factors      : list of human-readable contributing factors
    cargo_type   : cargo type (affects thresholds)
    priority     : "standard" | "emergency"

    Returns
    -------
    dict with keys:
        action              – "MONITOR" | "WARN" | "REROUTE" | "BLOCK_ROUTE" | "ESCALATE"
        priority            – "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
        road_id
        risk_score
        risk_level
        reason              – human-readable explanation
        factors             – contributing factors list
        cargo_type
        thresholds_applied  – "standard" | "emergency"
    """
    factors = factors or []
    thresholds = _get_thresholds(cargo_type, priority)
    action = _classify_action(risk_score, thresholds)
    thresh_name = "emergency" if thresholds is EMERGENCY_THRESHOLDS else "standard"

    # Escalate if CRITICAL and emergency medical cargo (takes priority over BLOCK_ROUTE)
    final_action = action.upper()
    if action == "block" and priority.lower() == "emergency":
        final_action = "ESCALATE"
    elif action == "block":
        final_action = "BLOCK_ROUTE"

    reason = _format_reason(action, risk_score, risk_level, factors, road_id)

    return {
        "action":             final_action,
        "priority":           PRIORITY_LEVELS[action],
        "road_id":            road_id,
        "risk_score":         round(risk_score, 4),
        "risk_level":         risk_level,
        "reason":             reason,
        "factors":            factors,
        "cargo_type":         cargo_type,
        "thresholds_applied": thresh_name,
    }


# ---------------------------------------------------------------------------
# Route-level action
# ---------------------------------------------------------------------------

def recommend_route_action(
    route_evaluation: dict[str, Any],
    cargo_type: str = "general",
    priority: str = "standard",
) -> dict[str, Any]:
    """
    Recommend an action given the full route evaluation output.

    Parameters
    ----------
    route_evaluation : output of routing.route_intelligence.evaluate_routes()
    cargo_type       : cargo type
    priority         : "standard" | "emergency"

    Returns
    -------
    dict with keys:
        action              – recommended action string
        priority            – urgency level
        recommended_route   – route_id of the recommended route
        reason              – human-readable reason
        route_comparison    – summary of fastest / safest / balanced with risks
        alternatives        – list of viable alternative routes
    """
    routes    = route_evaluation.get("routes", {})
    fastest   = route_evaluation.get("fastest")
    safest    = route_evaluation.get("safest")
    balanced  = route_evaluation.get("balanced")
    rec       = route_evaluation.get("recommended", {})
    rec_id    = rec.get("route_id", balanced or fastest)

    if not routes or not rec_id:
        return {
            "action":   "MONITOR",
            "priority": "LOW",
            "reason":   "No route data available.",
            "recommended_route": None,
        }

    # Get risk of the fastest (current) route
    fastest_risk = routes[fastest]["risk"] if fastest else 0.0
    rec_risk     = routes[rec_id]["risk"]
    thresholds   = _get_thresholds(cargo_type, priority)
    action       = _classify_action(fastest_risk, thresholds)

    # Build route comparison summary
    comparison = {}
    for rid, r in routes.items():
        h, m = divmod(r["eta_minutes"], 60)
        comparison[rid] = {
            "label":       r.get("label", rid),
            "eta":         f"{h}h {m:02d}m",
            "eta_minutes": r["eta_minutes"],
            "risk":        r["risk"],
            "risk_level":  r["risk_level"],
        }

    # Alternatives = all routes except the one we're recommending
    alternatives = [
        {"route_id": rid, "eta_minutes": r["eta_minutes"], "risk": r["risk"]}
        for rid, r in routes.items()
        if rid != rec_id
    ]
    alternatives.sort(key=lambda x: x["risk"])

    # Build reason
    if action == "monitor":
        reason = (
            f"All evaluated routes have acceptable risk levels. "
            f"Fastest route ({fastest}) is recommended. "
            f"Current risk: {fastest_risk:.0%}."
        )
        final_action = "MONITOR"
        final_priority = "LOW"
    elif action == "warn":
        reason = (
            f"Fastest route ({fastest}) has elevated risk ({fastest_risk:.0%}). "
            f"Route {rec_id} is recommended as a safer alternative "
            f"({rec_risk:.0%} risk)."
        )
        final_action = "WARN"
        final_priority = "MEDIUM"
    else:
        time_diff = routes[rec_id]["eta_minutes"] - routes[fastest]["eta_minutes"]
        risk_diff = fastest_risk - rec_risk
        reason = (
            f"Fastest route ({fastest}) has {fastest_risk:.0%} disruption risk — "
            f"above the {'emergency' if thresholds is EMERGENCY_THRESHOLDS else 'standard'} "
            f"threshold. Route {rec_id} recommended: {rec_risk:.0%} risk "
            f"(−{risk_diff:.0%}) with {time_diff:+d} min additional travel time. "
            f"{rec.get('reason', '')}"
        )
        final_action   = "BLOCK_ROUTE" if action == "block" else "REROUTE"
        final_priority = "CRITICAL"   if action == "block" else "HIGH"

        # Escalate for emergency cargo on blocked routes
        if action == "block" and priority.lower() == "emergency":
            final_action   = "ESCALATE"
            final_priority = "CRITICAL"

    return {
        "action":            final_action,
        "priority":          final_priority,
        "recommended_route": rec_id,
        "reason":            reason,
        "route_comparison":  comparison,
        "alternatives":      alternatives,
        "cargo_type":        cargo_type,
        "cargo_priority":    priority,
    }


# ---------------------------------------------------------------------------
# Smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🧠 NEXUS-NER | Decision Engine — Smoke Test")
    print("=" * 60)

    # Test single-road decisions
    test_cases = [
        ("NH13_042", 0.18, "SAFE",     ["Low rainfall"],         "general",  "standard"),
        ("NH13_042", 0.45, "MODERATE", ["Moderate rainfall"],    "general",  "standard"),
        ("NH13_042", 0.68, "HIGH",     ["Heavy rainfall", "Poor road condition"], "general", "standard"),
        ("NH13_042", 0.85, "CRITICAL", ["Extreme rain", "Steep slope"],           "medical", "emergency"),
    ]

    print("\n  Single-Road Decisions:")
    for road, risk, level, factors, cargo, prio in test_cases:
        result = recommend_action(
            risk_score=risk, risk_level=level,
            road_id=road, factors=factors,
            cargo_type=cargo, priority=prio,
        )
        print(f"\n    Risk: {risk:.0%} ({level}) | Cargo: {cargo}/{prio}")
        print(f"    Action: {result['action']:12s} | Priority: {result['priority']}")
        print(f"    Reason: {result['reason'][:80]}…")

    # Test route-level decision
    print("\n\n  Route-Level Decision (simulated):")
    mock_eval = {
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
    result = recommend_route_action(mock_eval, cargo_type="medical", priority="emergency")
    print(f"\n    Action    : {result['action']}")
    print(f"    Priority  : {result['priority']}")
    print(f"    Route     : {result['recommended_route']}")
    print(f"    Reason    : {result['reason'][:100]}…")

    print("\n✅ Decision engine OK")
