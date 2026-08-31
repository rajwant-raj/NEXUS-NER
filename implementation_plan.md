# NEXUS-NER — AI/ML Layer Implementation Plan

A complete build-out of the intelligence layer for NEXUS-NER, covering every module described in the team specification: data pipeline, feature engineering, disruption prediction, risk scoring, explainability, what-if simulation, route intelligence, and recommendation engine — all exposed as a clean REST API.

---

## Open Questions

> [!IMPORTANT]
> Please answer these before I start building, as they affect core architecture choices:

1. **Python environment** — Should I create a `requirements.txt` / `pyproject.toml`, or do you already have a Python environment set up? Any version constraint (e.g., Python 3.10+)?
2. **API framework** — Should the AI service be exposed via **FastAPI** (recommended, modern, async) or **Flask**? FastAPI is preferred for clean OpenAPI docs.
3. **Serving the API** — Should the AI service run standalone (e.g., `uvicorn` on port 8000) or be integrated into an existing backend server?
4. **SHAP** — SHAP can be slow to install / import. Should I include it as a hard dependency, or use a simpler feature-importance fallback for the prototype that can be swapped for SHAP later?
5. **Existing project code** — The `NEXUS/` folder currently only contains a Word document. Should the AI service live at `NEXUS/services/ai/` or a different path?

---

## Proposed Changes

### Module A — Data Pipeline & Dataset Generator

#### [NEW] `services/ai/data/generate_dataset.py`
Generates 10,000 realistic synthetic observations for roads across Northeast India (NH-13, NH-15, NH-37, etc.) with:
- Weather columns: `rainfall_1h`, `rainfall_3h`, `rainfall_6h`, `rainfall_24h`, `temperature`, `humidity`
- Road columns: `road_condition`, `road_age`, `maintenance_score`
- Traffic columns: `traffic_level`, `average_speed`
- Terrain columns: `slope`, `elevation`, `river_distance`
- Historical columns: `historical_incidents`, `incident_count_7d`, `incident_count_30d`, `previous_disruptions`
- Target: `disruption` (binary 0/1)

Label generation uses a realistic rule (high rainfall + poor road + high slope → higher probability of disruption) so the model has learnable signal.

#### [NEW] `services/ai/data/processed/dataset.csv`
Output of the generator — 10 000 rows, all columns above.

---

### Module B — Feature Engineering

#### [NEW] `services/ai/features/feature_engineering.py`
Scikit-learn `Pipeline`-compatible transformer that produces:
- **Weather**: `rainfall_intensity`, `rainfall_change`, `rainfall_accumulation`
- **Traffic**: `congestion_score`, `speed_deviation`
- **Historical**: `incident_frequency`, `disruption_frequency`, `historical_risk`
- **Road**: `road_condition_score` (composite)
- **Geographic**: `terrain_risk` (composite of slope + elevation + river_distance)

Returns a cleaned, scaled feature matrix ready for model training.

---

### Module C — Training & Evaluation

#### [NEW] `services/ai/training/train.py`
- Loads `dataset.csv`
- Applies feature engineering pipeline
- Stratified train/val/test split (70/15/15), no data leakage
- Trains **Logistic Regression** (baseline) and **Random Forest** (primary)
- Selects the best model by F1 (recall-weighted)
- Serializes winner to `models/risk_model.pkl`
- Saves `models/model_metadata.json` with all eval metrics

#### [NEW] `services/ai/training/evaluate.py`
Standalone script to load a saved model and print:
- Accuracy, Precision, Recall, F1, ROC-AUC
- Confusion matrix (ASCII + saved PNG)

#### [NEW] `services/ai/models/risk_model.pkl`
Serialized sklearn Pipeline (preprocessing + classifier).

#### [NEW] `services/ai/models/model_metadata.json`
```json
{
  "model_type": "RandomForestClassifier",
  "trained_at": "...",
  "features": [...],
  "metrics": { "accuracy": ..., "f1": ..., "roc_auc": ... },
  "note": "Trained on synthetic data. Do not present as real-world accuracy."
}
```

---

### Module D — Inference Engine

#### [NEW] `services/ai/inference/predictor.py`
- Loads the saved pipeline once at import time
- `predict(features: dict) → {"probability": float, "risk_level": str}`
- Validates inputs; raises clear errors for missing/out-of-range values
- Keeps inference < 50 ms for interactive use

---

### Module E — Risk Scoring Engine

#### [NEW] `services/ai/risk/risk_engine.py`
Weighted combination:
```
final_risk =
    0.40 × ml_probability
  + 0.20 × weather_risk
  + 0.15 × road_condition_risk
  + 0.10 × traffic_risk
  + 0.10 × historical_risk
  + 0.05 × accessibility_penalty
```
Categories: SAFE (0–0.25) / MODERATE (0.25–0.50) / HIGH (0.50–0.75) / CRITICAL (0.75–1.00)

---

### Module F — Explainability

#### [NEW] `services/ai/explainability/explainer.py`
- Primary: uses Random Forest `.feature_importances_` + input values to rank top-N contributing factors
- Secondary (optional): SHAP TreeExplainer when SHAP is installed
- Returns human-readable factor strings:
  ```
  ["Heavy rainfall", "Poor road condition", "High historical incident frequency", "Steep terrain"]
  ```

---

### Module G — What-If Simulator

#### [NEW] `services/ai/simulation/scenarios.py`
Pre-built scenarios:
| Scenario | rainfall_1h | road_condition | traffic_level |
|---|---|---|---|
| NORMAL | 10 | 0.85 | 0.20 |
| HEAVY_RAIN | 90 | 0.85 | 0.20 |
| EXTREME_RAIN | 150 | 0.85 | 0.20 |
| HIGH_TRAFFIC | 10 | 0.85 | 0.90 |
| POOR_ROAD | 10 | 0.20 | 0.20 |
| LANDSLIDE | 120 | 0.15 | 0.10 |
| COMBINED | 90 | 0.20 | 0.80 |

`run_scenario(name) → {scenario, probability, risk_level, factors, final_risk}`

---

### Module H — Route Intelligence

#### [NEW] `services/ai/routing/route_intelligence.py`
- Static route graph for `Guwahati → Tawang` (and other demo corridors) with per-segment road IDs
- Calculates per-route risk by aggregating segment-level risk scores
- `evaluate_routes(origin, destination, cargo_type, priority) → {fastest, safest, balanced}`
- Balanced cost: `α × normalized_time + (1-α) × risk`, where `α` is cargo-priority-dependent

---

### Module I — Recommendation Engine

#### [NEW] `services/ai/recommendations/decision_engine.py`
- Reads route evaluation output
- Applies thresholds: `risk > 0.75 → BLOCK_ROUTE`, `> 0.50 → REROUTE`, `> 0.25 → WARN`, else `MONITOR`
- Cargo-aware: emergency medical cargo uses stricter thresholds
- Returns: `{action, priority, recommended_route, reason}`

---

### Module J — FastAPI Service (AI API)

#### [NEW] `services/ai/api/main.py`
Three endpoints:
- `POST /ai/predict-risk` — calls predictor + risk engine + explainer
- `POST /ai/route-intelligence` — calls route intelligence
- `POST /ai/recommend-action` — calls decision engine
- `GET /ai/health` — health check
- `GET /ai/scenarios` — returns all what-if scenario results

#### [NEW] `services/ai/api/schemas.py`
Pydantic v2 request/response models exactly matching the API contract in the spec.

#### [NEW] `services/ai/api/middleware.py`
Request validation, error handling, CORS headers (for web team).

---

### Module K — Tests

#### [NEW] `services/ai/tests/test_features.py`
- Feature pipeline produces expected output shape
- No NaN in output
- Handles missing optional fields

#### [NEW] `services/ai/tests/test_model.py`
- Model loads correctly
- Prediction returns value in [0, 1]
- Edge cases: all-zero input, all-max input

#### [NEW] `services/ai/tests/test_risk.py`
- Risk score always in [0, 1]
- Risk categories match thresholds
- Factors list is non-empty

#### [NEW] `services/ai/tests/test_routing.py`
- Fastest ≤ balanced ≤ safest (time)
- Safest ≤ balanced ≤ fastest (risk)
- Risk changes when input risk changes

#### [NEW] `services/ai/tests/test_recommendations.py`
- High-risk route → REROUTE or BLOCK_ROUTE action
- Low-risk route → MONITOR
- Emergency cargo → stricter thresholds

---

### Infrastructure

#### [NEW] `services/ai/requirements.txt`
```
fastapi>=0.111
uvicorn[standard]>=0.29
scikit-learn>=1.4
numpy>=1.26
pandas>=2.2
joblib>=1.4
pydantic>=2.7
pytest>=8.2
matplotlib>=3.9
seaborn>=0.13
shap>=0.45   # optional, for full SHAP support
```

#### [NEW] `services/ai/README.md`
- Setup instructions
- How to generate data and train the model
- How to run the API
- API reference with example curl commands
- Architecture diagram (ASCII)
- Disclaimer: trained on synthetic data

---

## Verification Plan

### Automated
```bash
cd services/ai
python data/generate_dataset.py          # generates dataset.csv
python training/train.py                 # trains + saves model
python training/evaluate.py              # prints metrics
pytest tests/ -v                         # all unit tests
uvicorn api.main:app --reload            # starts API
```

### Demo Scenario Validation
Run `python simulation/scenarios.py` and confirm:
- NORMAL → ~18% risk (SAFE)
- HEAVY_RAIN → ~55–65% (HIGH)
- COMBINED → ~80%+ (CRITICAL)

### API Contract Validation
`curl -X POST /ai/predict-risk` with the exact sample payload from the spec → must return `probability`, `risk_level`, `factors`.

---

> [!NOTE]
> All synthetic data is clearly labelled. Model performance metrics in `model_metadata.json` include a mandatory disclaimer note. The system is designed so real data can replace synthetic data without changing any downstream code.
