"""
NEXUS-NER | API Schemas (Pydantic v2)
======================================
Request and response models for all AI API endpoints.
These exactly match the API contract defined in the team specification.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class RoadFeatures(BaseModel):
    """Raw feature input for a single road segment."""

    # Required
    rainfall_1h:         float = Field(..., ge=0, le=500,  description="Rainfall in last 1 hour (mm)")
    rainfall_3h:         float = Field(..., ge=0, le=1000, description="Rainfall in last 3 hours (mm)")
    traffic_level:       float = Field(..., ge=0, le=1.0,  description="Traffic congestion level [0–1]")
    road_condition:      float = Field(..., ge=0, le=1.0,  description="Road surface condition [0–1], 1=perfect")
    slope:               float = Field(..., ge=0, le=90,   description="Road slope in degrees")
    river_distance:      float = Field(..., ge=0, le=100,  description="Distance to nearest river (km)")
    historical_incidents: int  = Field(..., ge=0,          description="Total historical incidents on this road")

    # Optional (have defaults in the inference engine)
    rainfall_6h:         Optional[float] = Field(None, ge=0, le=1500)
    rainfall_24h:        Optional[float] = Field(None, ge=0, le=3000)
    temperature:         Optional[float] = Field(None, ge=-10, le=50)
    humidity:            Optional[float] = Field(None, ge=0, le=100)
    average_speed:       Optional[float] = Field(None, ge=0, le=150)
    road_age:            Optional[float] = Field(None, ge=0, le=100)
    maintenance_score:   Optional[float] = Field(None, ge=0, le=1.0)
    elevation:           Optional[float] = Field(None, ge=0, le=8848)
    incident_count_7d:  Optional[int]   = Field(None, ge=0)
    incident_count_30d: Optional[int]   = Field(None, ge=0)
    previous_disruptions: Optional[int] = Field(None, ge=0)

    def to_dict(self) -> dict:
        """Return only non-None values as a plain dict."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


# ---------------------------------------------------------------------------
# POST /ai/predict-risk
# ---------------------------------------------------------------------------

class PredictRiskRequest(BaseModel):
    road_id:  str          = Field(..., description="Unique road segment identifier")
    features: RoadFeatures = Field(..., description="Road and environmental features")


class PredictRiskResponse(BaseModel):
    road_id:     str        = Field(..., description="Road segment identifier")
    probability: float      = Field(..., ge=0, le=1, description="Disruption probability [0–1]")
    risk_level:  str        = Field(..., description="SAFE | MODERATE | HIGH | CRITICAL")
    final_risk:  float      = Field(..., ge=0, le=1, description="Composite risk score [0–1]")
    factors:     list[str]  = Field(default_factory=list, description="Top contributing risk factors")
    components:  dict       = Field(default_factory=dict, description="Individual risk signal breakdown")
    explain_method: str     = Field("feature_importance", description="Explanation method used")


# ---------------------------------------------------------------------------
# POST /ai/route-intelligence
# ---------------------------------------------------------------------------

class RouteIntelligenceRequest(BaseModel):
    origin:      str = Field(..., description="Departure location")
    destination: str = Field(..., description="Arrival location")
    cargo_type:  str = Field("general", description="Cargo type: medical | supplies | general | fuel")
    priority:    str = Field("standard", description="Priority: emergency | standard")


class RouteOption(BaseModel):
    route_id:    str
    label:       str
    description: str
    distance_km: float
    eta_minutes: int
    risk:        float
    risk_level:  str


class RecommendedRoute(BaseModel):
    route_id: str
    reason:   str


class RouteIntelligenceResponse(BaseModel):
    fastest:     RouteOption
    safest:      RouteOption
    balanced:    RouteOption
    recommended: RecommendedRoute
    all_routes:  list[RouteOption]
    metadata:    dict


# ---------------------------------------------------------------------------
# POST /ai/recommend-action  (single road)
# ---------------------------------------------------------------------------

class RecommendActionRequest(BaseModel):
    road_id:    str          = Field(..., description="Road segment identifier")
    features:   RoadFeatures = Field(..., description="Current road and weather conditions")
    cargo_type: str          = Field("general")
    priority:   str          = Field("standard")


class RecommendActionResponse(BaseModel):
    action:             str       = Field(..., description="MONITOR | WARN | REROUTE | BLOCK_ROUTE | ESCALATE")
    priority:           str       = Field(..., description="LOW | MEDIUM | HIGH | CRITICAL")
    road_id:            str
    risk_score:         float
    risk_level:         str
    reason:             str
    factors:            list[str]
    recommended_route:  Optional[str] = None
    cargo_type:         str
    thresholds_applied: str


# ---------------------------------------------------------------------------
# GET /ai/scenarios
# ---------------------------------------------------------------------------

class ScenarioResult(BaseModel):
    scenario:      str
    description:   str
    road_id:       str
    inputs:        dict
    ml_probability: float
    final_risk:    float
    risk_level:    str
    factors:       list[str]


class ScenariosResponse(BaseModel):
    scenarios: list[ScenarioResult]
    total:     int


# ---------------------------------------------------------------------------
# GET /ai/health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    model_type:   Optional[str] = None
    version:      str = "1.0.0"
    disclaimer:   str = (
        "⚠️ AI predictions are based on synthetic prototype data. "
        "Not for production use without real data retraining."
    )
