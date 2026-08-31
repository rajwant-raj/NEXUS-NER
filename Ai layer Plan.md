# 🤖 AI/ML TEAM — RESPONSIBILITIES & EXECUTION PLAN

## 1. Role Overview

The AI/ML team is responsible for building the **intelligence layer** of NEXUS-NER.

The web team is responsible for displaying the intelligence, and the backend team is responsible for connecting services and data.

The AI/ML team's job is to answer:

```text
What is likely to happen?
        ↓
How risky is it?
        ↓
Why is it risky?
        ↓
Which route is better?
        ↓
What should the system recommend?
```

### AI/ML responsibility pipeline

```text
RAW DATA
   ↓
DATA PREPROCESSING
   ↓
FEATURE ENGINEERING
   ↓
DISRUPTION PREDICTION
   ↓
RISK SCORING
   ↓
ROUTE INTELLIGENCE
   ↓
DECISION / RECOMMENDATION
   ↓
BACKEND API
   ↓
WEB / MOBILE
```

---

# 2. AI/ML Team Ownership

The AI/ML team owns the following components:

```text
1. Data Pipeline
2. Dataset Generation / Preparation
3. Feature Engineering
4. Road Disruption Prediction
5. Risk Scoring Engine
6. Explainable AI
7. Risk-Aware Route Intelligence
8. Recommendation / Decision Engine
9. AI API Integration
10. AI Testing & Evaluation
```

---

# 3. Primary AI/ML Goal

The main AI feature is:

> **Predict the probability that a road segment will experience a logistics disruption within a defined future time window.**

Example:

```text
Road: NH-13

Disruption Probability:
82%

Risk:
HIGH

Main Contributing Factors:
- Heavy rainfall
- Poor road condition
- High historical incident frequency
- Steep terrain
```

The prediction must then be used by the rest of the system.

```text
Prediction
    ↓
Risk Score
    ↓
Route Evaluation
    ↓
Recommendation
```

---

# 4. Module A — Data Pipeline

## Objective

Create a clean and reusable pipeline for preparing data for the ML models.

### Inputs

Potential features include:

```text
Weather
Road Condition
Traffic
Historical Incidents
Terrain
Slope
River Proximity
Previous Disruptions
Vehicle / Logistics Information
```

### Responsibilities

* [ ] Define data schema
* [ ] Collect available real/static data
* [ ] Generate realistic synthetic/demo data where real data is unavailable
* [ ] Clean missing values
* [ ] Validate ranges
* [ ] Normalize data where required
* [ ] Create train/validation/test splits
* [ ] Prevent data leakage
* [ ] Save processed datasets

### Important Rule

Synthetic data may be used for the prototype, but it must be clearly documented as simulated data.

Do **not** present synthetic-data performance as real-world production accuracy.

---

# 5. Module B — Dataset

## Objective

Create the main dataset used by the disruption model.

### Suggested dataset size

For the prototype:

```text
5,000–20,000 observations
```

depending on available compute and development time.

### Suggested columns

```text
road_id
latitude
longitude

rainfall_1h
rainfall_3h
rainfall_6h
rainfall_24h

temperature
humidity

traffic_level
average_speed

road_condition
road_age
maintenance_score

slope
elevation
river_distance

historical_incidents
incident_count_7d
incident_count_30d
previous_disruptions

disruption
```

### Target

```text
disruption
```

where:

```text
0 = no disruption
1 = disruption
```

### Deliverable

```text
services/ai/data/
    raw/
    processed/
    dataset.csv
    generate_dataset.py
```

---

# 6. Module C — Feature Engineering

## Objective

Convert raw data into features that represent meaningful transportation and environmental conditions.

### Weather Features

Create:

```text
rainfall_intensity
rainfall_change
rainfall_accumulation
rainfall_3h
rainfall_24h
```

### Traffic Features

Create:

```text
traffic_level
traffic_change
speed_deviation
congestion_score
```

### Historical Features

Create:

```text
historical_risk
incident_frequency
incident_count_7d
incident_count_30d
disruption_frequency
```

### Road Features

Create:

```text
road_condition_score
maintenance_score
road_age
```

### Geographic Features

Create:

```text
slope
elevation
river_distance
terrain_risk
```

### Deliverable

```text
services/ai/features/
    feature_engineering.py
```

---

# 7. Module D — Road Disruption Prediction Model

## Objective

Predict:

```text
P(disruption)
```

for a road segment.

### Recommended approach

Start with:

```text
Baseline:
Logistic Regression

Primary:
Random Forest

Optional comparison:
XGBoost
```

Do not start with deep learning unless the core system is already complete.

The prototype needs a reliable and explainable model more than an unnecessarily complex architecture.

---

# 8. Model Training

## Training pipeline

```text
Dataset
   ↓
Preprocessing
   ↓
Feature Engineering
   ↓
Train / Validation / Test Split
   ↓
Model Training
   ↓
Evaluation
   ↓
Model Selection
   ↓
Model Serialization
```

### Deliverables

```text
services/ai/training/
    train.py
    evaluate.py
```

Model:

```text
services/ai/models/
    risk_model.pkl
    model_metadata.json
```

---

# 9. Model Evaluation

The model must not be evaluated using accuracy alone.

Track:

```text
Accuracy
Precision
Recall
F1 Score
ROC-AUC
Confusion Matrix
```

### Important consideration

For disruption detection, **recall is important** because failing to identify a genuinely dangerous road can be more serious than generating an additional warning.

The chosen metric priorities should be documented along with the model.

---

# 10. Module E — Inference Engine

## Objective

Load the trained model and make predictions from new road/weather conditions.

### Input

Example:

```json
{
  "rainfall_1h": 88,
  "rainfall_3h": 205,
  "traffic_level": 0.72,
  "road_condition": 0.32,
  "slope": 18.4,
  "historical_incidents": 7,
  "river_distance": 0.9
}
```

### Output

```json
{
  "probability": 0.82,
  "risk_level": "HIGH"
}
```

### Deliverable

```text
services/ai/inference/
    predictor.py
```

---

# 11. Module F — Risk Scoring Engine

The ML prediction should **not** be the only factor determining final road risk.

The Risk Engine combines multiple signals.

```text
ML Prediction
      +
Weather
      +
Road Condition
      +
Traffic
      +
Historical Incidents
      +
Accessibility
      ↓
FINAL RISK SCORE
```

### Example

```text
final_risk =
    0.40 × ml_probability
  + 0.20 × weather_risk
  + 0.15 × road_condition_risk
  + 0.10 × traffic_risk
  + 0.10 × historical_risk
  + 0.05 × accessibility_penalty
```

Weights may be adjusted after testing.

### Risk categories

```text
0.00–0.25 → SAFE
0.25–0.50 → MODERATE
0.50–0.75 → HIGH
0.75–1.00 → CRITICAL
```

### Deliverable

```text
services/ai/risk/
    risk_engine.py
```

---

# 12. Module G — Explainable AI

## Objective

The system must explain **why** it considers a road dangerous.

The output should contain:

```text
Prediction
Risk Level
Top Contributing Factors
```

Example:

```text
Disruption Probability: 82%

Risk Level: HIGH

Main Factors:
1. Heavy rainfall
2. Poor road condition
3. High historical incident frequency
4. Steep terrain
```

### Possible implementation

Use:

```text
SHAP
```

or another suitable feature-importance/explanation method.

For a prototype, a simple and transparent feature-contribution approach is acceptable if it is documented correctly.

### Deliverable

```text
services/ai/explainability/
```

---

# 13. Module H — What-If Risk Simulator

## Objective

Allow the team to simulate environmental changes and observe AI output changes.

### Scenarios

```text
NORMAL
HEAVY RAIN
EXTREME RAIN
HIGH TRAFFIC
POOR ROAD CONDITION
LANDSLIDE
COMBINED DISRUPTION
```

### Example

Normal:

```text
Rainfall:
10 mm

Risk:
18%
```

Heavy Rain:

```text
Rainfall:
90 mm

Risk:
61%
```

Heavy Rain + Poor Road:

```text
Rainfall:
90 mm

Road:
Poor

Risk:
82%
```

### Purpose

This becomes an important part of the live SIH demonstration.

### Deliverable

```text
services/ai/simulation/
    scenarios.py
```

---

# 14. Module I — Route Intelligence

The AI/ML team works together with the GIS/routing team.

The ML team's responsibility is to provide the **risk intelligence** used by route optimization.

The routing team owns the geographic graph.

### Route evaluation

Each route should have:

```text
Travel Time
Distance
Risk
Accessibility
Traffic
Weather
Disruption Probability
```

Example:

```text
ROUTE A
ETA: 8h 02m
Risk: 78%

ROUTE B
ETA: 8h 39m
Risk: 21%

ROUTE C
ETA: 9h 18m
Risk: 17%
```

---

# 15. Fastest / Safest / Balanced Routes

The system should support:

```text
FASTEST
SAFEST
BALANCED
```

### Fastest

Prioritize:

```text
travel_time
```

### Safest

Prioritize:

```text
risk
```

### Balanced

Combine:

```text
travel_time
+
risk
```

---

# 16. Adaptive Route Recommendation

Route recommendations should depend on cargo priority.

### Emergency Medical Cargo

Risk receives greater weight.

```text
Risk Weight:
HIGH
```

### Normal Cargo

Travel time can receive greater weight.

```text
Risk Weight:
MEDIUM
```

### Example

```text
FASTEST:
8h
Risk = 78%

SAFEST:
9h 18m
Risk = 17%

BALANCED:
8h 39m
Risk = 31%
```

AI recommendation:

```text
BALANCED ROUTE

Reason:
Significantly reduces disruption risk
with only 37 minutes of additional travel time.
```

---

# 17. Module J — Recommendation Engine

## Objective

Convert model predictions into an actionable recommendation.

The system should answer:

```text
Should we reroute?
Which route?
Why?
How urgent is the action?
```

### Example

```json
{
  "action": "REROUTE",
  "priority": "HIGH",
  "recommended_route": "route_B",
  "reason": "Road disruption probability exceeded threshold"
}
```

### Possible actions

```text
MONITOR
WARN
REROUTE
BLOCK_ROUTE
ESCALATE
```

### Deliverable

```text
services/ai/recommendations/
    decision_engine.py
```

---

# 18. AI Decision Flow

```text
Weather
    ↓
Road Conditions
    ↓
Traffic
    ↓
Historical Incidents
    ↓
Terrain
    ↓
ML Prediction
    ↓
Risk Engine
    ↓
Route Evaluation
    ↓
Recommendation
    ↓
Alert / Reroute
```

---

# 19. AI API Contract

The AI team should expose clean interfaces to the backend team.

## Predict Risk

```text
POST /ai/predict-risk
```

### Input

```json
{
  "road_id": "NH13_042",
  "features": {
    "rainfall_1h": 90,
    "rainfall_3h": 210,
    "traffic_level": 0.75,
    "road_condition": 0.3,
    "slope": 18,
    "historical_incidents": 7
  }
}
```

### Response

```json
{
  "road_id": "NH13_042",
  "probability": 0.82,
  "risk_level": "HIGH",
  "factors": [
    "Heavy rainfall",
    "Poor road condition",
    "High historical incident frequency"
  ]
}
```

---

# 20. Route Intelligence API

```text
POST /ai/route-intelligence
```

### Input

```json
{
  "origin": "Guwahati",
  "destination": "Tawang",
  "cargo_type": "medical",
  "priority": "emergency"
}
```

### Response

```json
{
  "fastest": {
    "route_id": "route_a",
    "eta_minutes": 482,
    "risk": 0.78
  },
  "safest": {
    "route_id": "route_c",
    "eta_minutes": 558,
    "risk": 0.17
  },
  "balanced": {
    "route_id": "route_b",
    "eta_minutes": 519,
    "risk": 0.31
  },
  "recommended": {
    "route_id": "route_b",
    "reason": "Lower risk with limited additional travel time"
  }
}
```

---

# 21. Recommendation API

```text
POST /ai/recommend-action
```

### Response

```json
{
  "action": "REROUTE",
  "priority": "HIGH",
  "reason": "Current route has high predicted disruption probability",
  "recommended_route": "route_b"
}
```

---

# 22. AI/ML Folder Structure

```text
services/
└── ai/
    │
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── generate_dataset.py
    │
    ├── features/
    │   └── feature_engineering.py
    │
    ├── training/
    │   ├── train.py
    │   └── evaluate.py
    │
    ├── models/
    │   ├── risk_model.pkl
    │   └── model_metadata.json
    │
    ├── inference/
    │   └── predictor.py
    │
    ├── risk/
    │   └── risk_engine.py
    │
    ├── explainability/
    │   └── explainer.py
    │
    ├── simulation/
    │   └── scenarios.py
    │
    ├── routing/
    │   └── route_intelligence.py
    │
    ├── recommendations/
    │   └── decision_engine.py
    │
    └── tests/
        ├── test_features.py
        ├── test_model.py
        ├── test_risk.py
        ├── test_routing.py
        └── test_recommendations.py
```

---

# 23. AI/ML Development Schedule

## DAY 1 — Design

* [ ] Define prediction target
* [ ] Define feature schema
* [ ] Define data format
* [ ] Define risk formula
* [ ] Define API contracts
* [ ] Create AI folder structure

### Deliverable

AI architecture complete.

---

# DAY 2 — Dataset

* [ ] Create data generator
* [ ] Create realistic synthetic data
* [ ] Validate data
* [ ] Save dataset
* [ ] Define target labels

### Deliverable

```text
dataset.csv
```

---

# DAY 3 — Feature Engineering

* [ ] Weather features
* [ ] Traffic features
* [ ] Historical features
* [ ] Road features
* [ ] Geographic features
* [ ] Preprocessing pipeline

### Deliverable

Reusable feature pipeline.

---

# DAY 4 — Baseline Models

Train:

```text
Logistic Regression
Random Forest
```

Evaluate:

```text
Precision
Recall
F1
ROC-AUC
```

Choose the initial best-performing model.

---

# DAY 5 — Final Prediction Model

* [ ] Train final model
* [ ] Tune if necessary
* [ ] Evaluate
* [ ] Save model
* [ ] Create inference function

### Deliverable

```text
risk_model.pkl
predictor.py
```

---

# DAY 6 — Explainability

* [ ] Feature importance
* [ ] SHAP/equivalent
* [ ] Human-readable factors
* [ ] Explanation output

### Deliverable

Prediction + reason.

---

# DAY 7 — Risk Engine

* [ ] Combine ML + rules
* [ ] Weather risk
* [ ] Road risk
* [ ] Traffic risk
* [ ] Historical risk
* [ ] Accessibility penalty
* [ ] Risk categories

### Deliverable

```text
risk_engine.py
```

---

# DAY 8 — Route Intelligence

* [ ] Route risk
* [ ] Fastest route
* [ ] Safest route
* [ ] Balanced route
* [ ] Risk-weighted cost
* [ ] Route comparison

### Coordinate with GIS team.

---

# DAY 9 — Recommendation Engine

* [ ] Reroute decision
* [ ] Risk thresholds
* [ ] Cargo priorities
* [ ] Recommendation reasons
* [ ] Action priorities

---

# DAY 10 — Backend Integration

Coordinate with backend team.

Integrate:

```text
AI → Backend
```

Endpoints:

```text
/ai/predict-risk
/ai/route-intelligence
/ai/recommend-action
```

---

# DAY 11 — Live Data Integration

Replace purely static inputs with application data.

AI should consume:

```text
Weather
Road
Traffic
Incident
Vehicle
```

data from the platform.

---

# DAY 12 — Scenario Testing

Test:

```text
NORMAL
HEAVY RAIN
POOR ROAD
TRAFFIC JAM
LANDSLIDE
ROAD BLOCKAGE
COMBINED EVENT
```

Ensure risk and recommendations change logically.

---

# DAY 13 — Validation & Optimization

Check:

* [ ] Model errors
* [ ] Edge cases
* [ ] Missing data
* [ ] Invalid input
* [ ] Inference speed
* [ ] Risk consistency
* [ ] Route consistency
* [ ] Recommendation consistency

---

# DAY 14 — AI Freeze

Do not introduce a major new model.

Complete:

* [ ] Documentation
* [ ] Metrics
* [ ] Architecture diagram
* [ ] Demo scenario
* [ ] Sample predictions
* [ ] Final integration
* [ ] Presentation material

---

# 24. AI/ML Team Deliverables

By the end of the project, the AI/ML team must provide:

```text
✅ Dataset pipeline
✅ Feature engineering pipeline
✅ Trained disruption model
✅ Model evaluation
✅ Model inference
✅ Risk scoring engine
✅ Explainability
✅ What-if simulation
✅ Route intelligence
✅ Recommendation engine
✅ AI API contracts
✅ Tests
✅ AI documentation
```

---

# 25. Definition of Done — AI/ML

An AI feature is considered complete only when:

```text
Model / Logic
     +
Input Validation
     +
Inference
     +
Output
     +
Testing
     +
Documentation
```

are complete.

A notebook containing a trained model is **not** considered a finished feature.

---

# 26. AI/ML Testing Checklist

## Data

* [ ] Missing values
* [ ] Invalid values
* [ ] Outliers
* [ ] Data leakage checks

## Model

* [ ] Prediction works
* [ ] Saved model loads correctly
* [ ] Evaluation metrics recorded
* [ ] Edge cases tested

## Risk

* [ ] Risk score in valid range
* [ ] Risk categories correct
* [ ] Factors correctly identified

## Routing

* [ ] Fastest route works
* [ ] Safest route works
* [ ] Balanced route works
* [ ] Route changes when risk changes

## Recommendation

* [ ] Correct thresholds
* [ ] Correct action
* [ ] Correct priority
* [ ] Human-readable explanation

---

# 27. AI/ML Demo Scenario

The AI team should prepare the data and logic for the following scenario.

## Initial Condition

```text
Road:
NH-13

Rainfall:
10 mm

Road Condition:
Good

Traffic:
Low

Historical Risk:
Low
```

Prediction:

```text
Disruption Probability:
18%

Risk:
SAFE
```

---

## Trigger Heavy Rain

```text
Rainfall:
90 mm
```

Prediction:

```text
Disruption Probability:
61%

Risk:
HIGH
```

---

## Add Poor Road Condition

```text
Road Condition:
Poor
```

Prediction:

```text
Disruption Probability:
82%

Risk:
CRITICAL
```

---

## Route Evaluation

```text
Route A
Risk: 78%
ETA: 8h 02m

Route B
Risk: 21%
ETA: 8h 39m

Route C
Risk: 17%
ETA: 9h 18m
```

Recommendation:

```text
Route B

Reason:
Significantly lower predicted disruption risk
with limited additional travel time.
```

---

# 28. AI/ML Final Demo Message

When the judges ask:

### "Where is the AI?"

Answer:

> **Our AI engine predicts road-disruption probability using weather, terrain, road-condition, traffic, and historical incident features. That prediction feeds a dynamic risk engine, which evaluates route alternatives and recommends the most suitable route based on risk, travel time, accessibility, and cargo priority.**

### When asked:

### "What happens after prediction?"

Answer:

```text
Prediction
   ↓
Risk Score
   ↓
Route Evaluation
   ↓
Recommendation
   ↓
Alert / Reroute
```

The AI is therefore part of the operational decision loop rather than being an isolated prediction model.

---

# 29. AI/ML Team Rules

### Rule 1

Do not build complicated models before the basic model works.

### Rule 2

Do not claim real-world accuracy from synthetic data.

### Rule 3

Every prediction must have a defined input and output.

### Rule 4

AI outputs must be usable by the backend.

### Rule 5

Keep inference fast enough for interactive use.

### Rule 6

Explain important predictions.

### Rule 7

Do not create an AI chatbot unless the core intelligence is already complete.

### Rule 8

Coordinate API contracts with the backend team.

### Rule 9

Coordinate route-risk data with the GIS/routing team.

### Rule 10

By Day 14, prioritize reliability over experimentation.

---

# 30. AI/ML Priority Levels

## 🔴 P0 — Must Complete

```text
✅ Dataset
✅ Feature Engineering
✅ Disruption Prediction
✅ Risk Score
✅ Risk Categories
✅ Route Risk
✅ Recommendation Engine
✅ API Integration
```

## 🟡 P1 — Complete After P0

```text
✅ Explainability
✅ SHAP
✅ What-if Simulation
✅ Advanced Route Scoring
✅ Model Comparison
```

## 🟢 P2 — Optional

```text
Advanced Deep Learning
Satellite Image ML
Computer Vision
LLM Assistant
Reinforcement Learning
Advanced Forecasting
```

---

# 31. AI/ML Final Architecture

```text
                 DATA SOURCES
                      │
        ┌─────────────┼─────────────┐
        │             │             │
     Weather        Roads        Incidents
        │             │             │
        └─────────────┼─────────────┘
                      ↓
             DATA PREPROCESSING
                      ↓
             FEATURE ENGINEERING
                      ↓
             DISRUPTION MODEL
                      ↓
                PROBABILITY
                      ↓
               RISK ENGINE
                      ↓
           ┌──────────┴──────────┐
           │                     │
      EXPLAINABILITY       ROUTE INTELLIGENCE
           │                     │
           └──────────┬──────────┘
                      ↓
             RECOMMENDATION
                      ↓
                   BACKEND
                      ↓
               WEB / MOBILE
```

---

# 32. Final AI/ML Objective

The AI/ML team's job is **not simply to train a model**.

The goal is:

```text
DATA
 ↓
PREDICTION
 ↓
RISK
 ↓
EXPLANATION
 ↓
DECISION
 ↓
ACTION
```

### The final AI system should answer:

> **“What is likely to happen, how serious is it, why is it happening, which option is better, and what should we do?”**

That is the intelligence layer of NEXUS-NER.
