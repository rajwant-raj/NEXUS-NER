"""
NEXUS-NER | FastAPI Main Application
=====================================
AI/ML service exposing the full intelligence pipeline via REST API.

Endpoints
---------
    GET  /ai/health               – Health check + model status
    GET  /ai/scenarios            – Run all what-if scenarios
    POST /ai/predict-risk         – Predict disruption probability for a road segment
    POST /ai/route-intelligence   – Evaluate route alternatives
    POST /ai/recommend-action     – Get actionable recommendation for a road segment

Running
-------
    cd services/ai
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Docs available at: http://localhost:8000/docs
"""

import json
import sys
import time
import traceback
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure AI root is on the path
AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

from api.schemas import (
    PredictRiskRequest, PredictRiskResponse,
    RouteIntelligenceRequest, RouteIntelligenceResponse, RouteOption, RecommendedRoute,
    RecommendActionRequest, RecommendActionResponse,
    ScenariosResponse, ScenarioResult,
    HealthResponse,
)


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NEXUS-NER AI/ML Service",
    description=(
        "Intelligence layer for NEXUS-NER logistics risk management system.\n\n"
        "Provides road disruption prediction, risk scoring, route intelligence, "
        "and actionable recommendations.\n\n"
        "⚠️ **Prototype**: Predictions are based on synthetic training data."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — allow the web team to call this from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    response.headers["X-Process-Time-Ms"] = str(round(elapsed * 1000, 1))
    return response


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, ValueError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "type": "validation_error"},
        )
    if isinstance(exc, FileNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": str(exc),
                "type": "model_not_found",
                "hint": "Run python training/train.py to train the model first.",
            },
        )
    # Unexpected error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# ---------------------------------------------------------------------------
# Model metadata cache
# ---------------------------------------------------------------------------

_model_metadata: dict = {}


def _get_model_metadata() -> dict:
    global _model_metadata
    if not _model_metadata:
        meta_path = AI_ROOT / "models" / "model_metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                _model_metadata = json.load(f)
    return _model_metadata


# ---------------------------------------------------------------------------
# GET /ai/health
# ---------------------------------------------------------------------------

@app.get(
    "/ai/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
)
async def health_check():
    """Check if the AI service and model are ready."""
    meta = _get_model_metadata()
    model_path = AI_ROOT / "models" / "risk_model.pkl"
    model_loaded = model_path.exists() and bool(meta.get("model_type"))
    model_type = meta.get("model_type") if model_loaded else None

    if not model_loaded:
        model_type = "NOT_TRAINED — run python training/train.py"

    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        model_type=model_type,
    )


# ---------------------------------------------------------------------------
# GET /ai/scenarios
# ---------------------------------------------------------------------------

@app.get(
    "/ai/scenarios",
    response_model=ScenariosResponse,
    tags=["Simulation"],
    summary="Run all what-if scenarios",
)
async def get_scenarios(road_id: str = "NH13_042"):
    """
    Run all pre-defined what-if scenarios and return risk predictions for each.
    Useful for demonstration and testing.
    """
    from simulation.scenarios import run_all_scenarios

    raw = run_all_scenarios(road_id=road_id)
    results = []
    for r in raw:
        if "error" in r:
            continue
        results.append(ScenarioResult(
            scenario=r["scenario"],
            description=r["description"],
            road_id=r["road_id"],
            inputs=r["inputs"],
            ml_probability=r["ml_probability"],
            final_risk=r["final_risk"],
            risk_level=r["risk_level"],
            factors=r["factors"],
        ))

    return ScenariosResponse(scenarios=results, total=len(results))


# ---------------------------------------------------------------------------
# POST /ai/predict-risk
# ---------------------------------------------------------------------------

@app.post(
    "/ai/predict-risk",
    response_model=PredictRiskResponse,
    tags=["Prediction"],
    summary="Predict road disruption risk",
)
async def predict_risk(request: PredictRiskRequest):
    """
    Predict disruption probability for a road segment given current conditions.

    Returns the ML probability, composite risk score, risk level, and
    top contributing factors.
    """
    from inference.predictor import predict
    from risk.risk_engine import compute_risk
    from explainability.explainer import explain

    feat_dict = request.features.to_dict()

    # 1. ML prediction
    pred = predict(feat_dict)
    ml_prob = pred["probability"]

    # 2. Risk score
    risk_result = compute_risk(
        ml_probability=ml_prob,
        rainfall_1h=feat_dict["rainfall_1h"],
        rainfall_3h=feat_dict["rainfall_3h"],
        rainfall_24h=feat_dict.get("rainfall_24h", 0),
        humidity=feat_dict.get("humidity", 70),
        temperature=feat_dict.get("temperature", 22),
        road_condition=feat_dict["road_condition"],
        maintenance_score=feat_dict.get("maintenance_score", 0.70),
        road_age=feat_dict.get("road_age", 10),
        traffic_level=feat_dict["traffic_level"],
        average_speed=feat_dict.get("average_speed", 40),
        historical_incidents=feat_dict["historical_incidents"],
        incident_count_7d=feat_dict.get("incident_count_7d", 0),
        incident_count_30d=feat_dict.get("incident_count_30d", 0),
        previous_disruptions=feat_dict.get("previous_disruptions", 0),
        slope=feat_dict["slope"],
        river_distance=feat_dict["river_distance"],
        elevation=feat_dict.get("elevation", 500),
    )

    # 3. Explainability
    expl = explain(feat_dict, ml_probability=ml_prob)

    return PredictRiskResponse(
        road_id=request.road_id,
        probability=ml_prob,
        risk_level=pred["risk_level"],
        final_risk=risk_result["final_risk"],
        factors=expl["factors"],
        components=risk_result["components"],
        explain_method=expl["method"],
    )


# ---------------------------------------------------------------------------
# POST /ai/route-intelligence
# ---------------------------------------------------------------------------

@app.post(
    "/ai/route-intelligence",
    response_model=RouteIntelligenceResponse,
    tags=["Routing"],
    summary="Evaluate route alternatives with risk intelligence",
)
async def route_intelligence(request: RouteIntelligenceRequest):
    """
    Evaluate available routes between two locations and return
    fastest, safest, and balanced options with disruption risk scores.
    """
    from routing.route_intelligence import evaluate_routes

    try:
        result = evaluate_routes(
            origin=request.origin,
            destination=request.destination,
            cargo_type=request.cargo_type,
            priority=request.priority,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    routes = result["routes"]
    fastest_id  = result["fastest"]
    safest_id   = result["safest"]
    balanced_id = result["balanced"]
    rec         = result["recommended"]

    def _to_route_option(rid: str) -> RouteOption:
        r = routes[rid]
        return RouteOption(
            route_id=rid,
            label=r.get("label", rid),
            description=r.get("description", ""),
            distance_km=r.get("distance_km", 0),
            eta_minutes=r["eta_minutes"],
            risk=r["risk"],
            risk_level=r["risk_level"],
        )

    all_options = [_to_route_option(rid) for rid in routes]

    return RouteIntelligenceResponse(
        fastest=_to_route_option(fastest_id),
        safest=_to_route_option(safest_id),
        balanced=_to_route_option(balanced_id),
        recommended=RecommendedRoute(
            route_id=rec["route_id"],
            reason=rec["reason"],
        ),
        all_routes=all_options,
        metadata=result["metadata"],
    )


# ---------------------------------------------------------------------------
# POST /ai/recommend-action
# ---------------------------------------------------------------------------

@app.post(
    "/ai/recommend-action",
    response_model=RecommendActionResponse,
    tags=["Recommendation"],
    summary="Get actionable recommendation for a road segment",
)
async def recommend_action(request: RecommendActionRequest):
    """
    Run the full pipeline (predict → risk score → explain → decide) and
    return a concrete actionable recommendation.

    Possible actions: MONITOR | WARN | REROUTE | BLOCK_ROUTE | ESCALATE
    """
    from inference.predictor import predict
    from risk.risk_engine import compute_risk
    from explainability.explainer import explain
    from recommendations.decision_engine import recommend_action as _recommend

    feat_dict = request.features.to_dict()

    # Full pipeline
    pred = predict(feat_dict)
    ml_prob = pred["probability"]

    risk_result = compute_risk(
        ml_probability=ml_prob,
        rainfall_1h=feat_dict["rainfall_1h"],
        rainfall_3h=feat_dict["rainfall_3h"],
        rainfall_24h=feat_dict.get("rainfall_24h", 0),
        humidity=feat_dict.get("humidity", 70),
        temperature=feat_dict.get("temperature", 22),
        road_condition=feat_dict["road_condition"],
        maintenance_score=feat_dict.get("maintenance_score", 0.70),
        road_age=feat_dict.get("road_age", 10),
        traffic_level=feat_dict["traffic_level"],
        average_speed=feat_dict.get("average_speed", 40),
        historical_incidents=feat_dict["historical_incidents"],
        incident_count_7d=feat_dict.get("incident_count_7d", 0),
        incident_count_30d=feat_dict.get("incident_count_30d", 0),
        previous_disruptions=feat_dict.get("previous_disruptions", 0),
        slope=feat_dict["slope"],
        river_distance=feat_dict["river_distance"],
        elevation=feat_dict.get("elevation", 500),
    )

    expl = explain(feat_dict, ml_probability=ml_prob)

    decision = _recommend(
        risk_score=risk_result["final_risk"],
        risk_level=risk_result["risk_level"],
        road_id=request.road_id,
        factors=expl["factors"],
        cargo_type=request.cargo_type,
        priority=request.priority,
    )

    return RecommendActionResponse(
        action=decision["action"],
        priority=decision["priority"],
        road_id=request.road_id,
        risk_score=decision["risk_score"],
        risk_level=decision["risk_level"],
        reason=decision["reason"],
        factors=decision["factors"],
        recommended_route=None,   # use /ai/route-intelligence for route recommendation
        cargo_type=decision["cargo_type"],
        thresholds_applied=decision["thresholds_applied"],
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"])
async def root():
    return {
        "service":     "NEXUS-NER AI/ML Service",
        "version":     "1.0.0",
        "status":      "running",
        "docs":        "/docs",
        "endpoints": [
            "GET  /ai/health",
            "GET  /ai/scenarios",
            "POST /ai/predict-risk",
            "POST /ai/route-intelligence",
            "POST /ai/recommend-action",
        ],
    }
