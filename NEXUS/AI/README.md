# NEXUS-NER — Multi-Modal Logistics Intelligence & Risk Management

> 🌐 **NEXUS-NER** is an AI-powered intelligence platform built for logistics risk management across high-vulnerability transport corridors (specialized for Northeast India). It delivers real-time road disruption prediction, multi-signal composite risk scoring, route intelligence, explainable AI factors, and automated dispatch decision recommendations.

---

## 🏗️ Project Architecture

```
                                  [ RAW DATA STREAMS ]
                   (Weather Radar, Road Condition Sensors, Traffic Feeds)
                                            │
                                            ▼
                              [ 1. DATA PREPROCESSING ]
                                            │
                                            ▼
                           [ 2. FEATURE TRANSFORMER (25-D) ]
                            (Intensity, Terrain, Congestion)
                                            │
                                            ▼
                           [ 3. DISRUPTION PREDICTION MODEL ]
                            (Balanced Logistic / Random Forest)
                                            │
                                            ▼
                           [ 4. COMPOSITE RISK SCORING ]
                      (0.40·ML + 0.20·Weather + 0.15·Road + ...)
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
         [ 5. EXPLAINABILITY (XAI) ]                    [ 6. ROUTE INTELLIGENCE ]
       (Feature Importance & Key Drivers)             (Fastest / Safest / Balanced)
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            ▼
                             [ 7. DECISION RECOMMENDATION ]
                       (MONITOR | WARN | REROUTE | BLOCK | ESCALATE)
                                            │
                                            ▼
                               [ 8. FASTAPI SERVICE LAYER ]
                              (REST Endpoints on Port 8000)
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
     [ 9. SERVICES TESTING DASHBOARD ]                 [ 10. PRODUCTION CLIENTS ]
     (Interactive HTML/CSS/JS in frontend/)            (Web / Mobile Frontend Teams)
```

---

## 📂 Repository Structure

```
NEXUS/
│
├── frontend/                        # 🖥️ Interactive Web Test Suite & Dashboard
│   ├── index.html                   # 9-tab testing interface (Health, Transformer, Routing, etc.)
│   ├── style.css                    # Dark-mode glassmorphic theme with responsive grids
│   └── app.js                       # Live feature calculator & automated API test runner
│
├── services/
│   └── ai/                          # 🧠 AI/ML Core Service
│       ├── data/
│       │   ├── generate_dataset.py  # Module A: Synthetic 10,000-row road dataset generator
│       │   └── processed/           # Processed datasets (dataset.csv)
│       │
│       ├── features/
│       │   └── feature_engineering.py # Module B: 25-feature Sklearn transformer
│       │
│       ├── training/
│       │   ├── train.py             # Module C: Multi-model training & model selection
│       │   └── evaluate.py          # Standalone classification report & metrics evaluator
│       │
│       ├── models/                  # Serialized artifacts (risk_model.pkl, metadata.json)
│       │
│       ├── inference/
│       │   └── predictor.py         # Module D: In-memory singleton inference engine
│       │
│       ├── risk/
│       │   └── risk_engine.py       # Module E: Multi-signal weighted risk formula
│       │
│       ├── explainability/
│       │   └── explainer.py         # Module F: Human-readable key factor extractor
│       │
│       ├── simulation/
│       │   └── scenarios.py         # Module G: What-If simulation engine (7 demo scenarios)
│       │
│       ├── routing/
│       │   └── route_intelligence.py # Module H: Route graph & risk-penalty evaluator
│       │
│       ├── recommendations/
│       │   └── decision_engine.py   # Module I: Action classifier with medical emergency logic
│       │
│       ├── api/
│       │   ├── main.py              # Module J: FastAPI application (5 REST endpoints + CORS)
│       │   └── schemas.py           # Pydantic v2 data validation models
│       │
│       ├── tests/                   # 🧪 Pytest Suite (79 Automated Tests)
│       │   ├── test_features.py     # Feature shape & monotonicity tests
│       │   ├── test_model.py        # Model serialization & inference tests
│       │   ├── test_risk.py         # Risk normalization & threshold tests
│       │   ├── test_routing.py      # Route graphs & corridor tests
│       │   └── test_recommendations.py # Action thresholds & escalation tests
│       │
│       ├── conftest.py              # Test configuration & path setup
│       ├── README.md                # Dedicated AI service documentation
│       └── requirements.txt         # Service dependencies
│
├── pyrightconfig.json               # IDE language server configuration for venv
└── README.md                        # Project root documentation (this file)
```

---

## ⚡ Quick Start Guide

### 1. Environment Setup

```powershell
# Navigate to the project root
cd c:\Users\ASUS\Desktop\Program\Project\NEXUS

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r services/ai/requirements.txt
```

### 2. Generate Data & Train Model

```powershell
# Step A: Generate synthetic training dataset (10,000 observations)
python services/ai/data/generate_dataset.py

# Step B: Train baseline & primary models (saves risk_model.pkl)
python services/ai/training/train.py

# Step C: Evaluate model metrics
python services/ai/training/evaluate.py
```

### 3. Run Automated Tests

```powershell
# Execute the full 79-test suite
pytest services/ai/tests/ -v
```

### 4. Start the AI Backend Server

```powershell
# Start FastAPI service on port 8000
uvicorn services.ai.api.main:app --reload --port 8000
```
* **Interactive OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Launch the Web Testing Interface

Simply open [`frontend/index.html`](file:///c:/Users/ASUS/Desktop/Program/Project/NEXUS/frontend/index.html) in your browser:
* Double-click the file in File Explorer or open via your browser.
* Access the **🧪 Auto Test Suite** tab to run end-to-end integration tests directly from the UI.

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description | Request / Query Sample |
|---|---|---|---|
| `GET` | `/ai/health` | Service health, ping latency & model loading status | *None* |
| `GET` | `/ai/scenarios` | Run 7 batch what-if simulation scenarios | `?road_id=NH13_042` |
| `POST` | `/ai/predict-risk` | Predict disruption probability & get top risk factors | `{"road_id": "NH13_042", "features": {...}}` |
| `POST` | `/ai/route-intelligence` | Compare Fastest, Safest & Balanced routes | `{"origin": "Guwahati", "destination": "Tawang", "cargo_type": "medical", "priority": "emergency"}` |
| `POST` | `/ai/recommend-action` | End-to-end operational dispatch decision | `{"road_id": "NH13_042", "features": {...}, "cargo_type": "medical", "priority": "emergency"}` |

---

## 🧮 Composite Risk Scoring Formula

$$\text{final\_risk} = 0.40 \cdot P_{\text{ML}} + 0.20 \cdot R_{\text{Weather}} + 0.15 \cdot R_{\text{Road}} + 0.10 \cdot R_{\text{Traffic}} + 0.10 \cdot R_{\text{History}} + 0.05 \cdot R_{\text{Access}}$$

| Risk Range | Category | Standard Cargo Action | Emergency / Medical Cargo Action |
|---|---|---|---|
| `0.00 – 0.25` | **SAFE** | `MONITOR` | `MONITOR` |
| `0.25 – 0.50` | **MODERATE** | `WARN` | `WARN` (Lower threshold $\ge 0.20$) |
| `0.50 – 0.75` | **HIGH** | `REROUTE` | `REROUTE` (Lower threshold $\ge 0.40$) |
| `0.75 – 1.00` | **CRITICAL** | `BLOCK_ROUTE` | `ESCALATE` (Immediate Human Intervention) |

---

## 🖥️ Web Testing Dashboard Overview

The [`frontend/`](file:///c:/Users/ASUS/Desktop/Program/Project/NEXUS/frontend/) test interface includes 9 specialized verification modules:

1. **◉ System Health**: Real-time ping, uptime, latency indicator, active model identifier.
2. **⚙️ Feature Transformer**: Live interactive calculation replicating the 25-feature Sklearn transformer.
3. **🎯 Predict & Explain**: Parameter sliders, dynamic probability gauge, and XAI contributing factors.
4. **⚖️ Multi-Signal Risk**: Visual formula inspector with component weight breakdown.
5. **🗺️ Route Intelligence**: Multi-corridor route evaluation matrix (Guwahati $\leftrightarrow$ Tawang, Aizawl, Itanagar).
6. **🧠 Decision Engine**: Action classifier testing with standard vs emergency medical rules.
7. **⚡ Scenario Lab**: One-click batch runner for 7 SIH demo scenarios (`NORMAL` to `LANDSLIDE`).
8. **📊 Model & Metrics**: Validation vs test split metrics table (Accuracy, Precision, Recall, F1, AUC).
9. **🧪 Auto Test Suite**: In-browser test runner verifying all 5 backend endpoints simultaneously.

---

## ⚠️ Prototype Disclaimer

> All machine learning models, simulated sensors, and predictions in this repository are currently trained on **synthetic data** designed for prototype and demonstration purposes (SIH). Model accuracy metrics reflect synthetic distribution performance and should be retrained on real-world telemetry and meteorological data prior to mission-critical field deployment.
