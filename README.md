🚚 NEXUS-NER

AI-Based Smart Logistics & Accessibility Intelligence Platform for the North Eastern Region

«Smart India Hackathon 2026 — SIH26002»

NEXUS-NER is an AI-powered logistics intelligence and decision-support platform designed to improve transportation accessibility, route reliability, shipment visibility, and disruption response across the North Eastern Region (NER) of India.

The platform combines logistics management, route intelligence, accessibility scoring, real-time tracking, disruption detection, predictive AI/ML, and analytics into a unified system.

«Core Principle: AI should improve logistics decisions — not simply provide a chatbot.»

---

🎯 Project Goal

NEXUS-NER helps logistics operators answer:

- 🚚 Where is the shipment?
- 🗺️ Which route is best?
- ⚠️ What risks affect the route?
- 🌧️ How will weather or disruptions affect delivery?
- ⏱️ What is the predicted ETA?
- 📉 How much delay is expected?
- 🔄 Should the shipment be rerouted?
- 🛣️ Which alternative route is safer and more reliable?

Core Workflow

Create Shipment
      ↓
Generate Routes
      ↓
Evaluate Accessibility
      ↓
Calculate Route Risk
      ↓
Recommend Best Route
      ↓
Track Shipment
      ↓
Detect Disruption
      ↓
Predict Delay / ETA
      ↓
Recalculate Risk
      ↓
Recommend Alternative Route
      ↓
Generate Alert

---

🌏 Why NEXUS-NER?

The North Eastern Region presents unique logistics challenges such as:

- Difficult terrain
- Heavy rainfall
- Floods
- Landslides
- Road closures
- Traffic congestion
- Connectivity gaps
- Infrastructure limitations
- State boundaries
- Transportation constraints
- Delivery delays
- Unreliable routes
- Emergency rerouting

NEXUS-NER aims to make logistics more predictable, accessible, resilient, and data-driven.

---

🧠 Core Features

1. 🔐 Authentication & RBAC

Role-based access for:

- "ADMIN"
- "OPERATOR"
- "TRANSPORTER"
- "ANALYST"

Features:

- Registration
- Login
- Logout
- JWT authentication
- Token refresh
- Role-based authorization

---

2. 🚚 Shipment Management

Central entity of the platform.

Shipment Information

Tracking ID
Sender
Receiver
Origin
Destination
Cargo Type
Cargo Weight
Cargo Value
Transport Mode
Vehicle
Route
Priority
Status
Expected Delivery
Actual Delivery
Risk Score

Shipment Lifecycle

CREATED
   ↓
ASSIGNED
   ↓
PICKED_UP
   ↓
IN_TRANSIT
   ↓
OUT_FOR_DELIVERY
   ↓
DELIVERED

Failure states:

DELAYED
BLOCKED
CANCELLED
LOST
RETURNED

---

🗺️ 3. Route Intelligence

The platform generates and compares multiple routes.

Example

ROUTE A
Distance: 520 km
ETA: 15 hrs
Risk: 22%
Accessibility: High

ROUTE B
Distance: 480 km
ETA: 13 hrs
Risk: 41%
Accessibility: Medium

ROUTE C
Distance: 610 km
ETA: 18 hrs
Risk: 12%
Accessibility: Very High

The system recommends the most suitable route based on:

ETA
Distance
Risk
Accessibility
Weather
Terrain
Traffic
Infrastructure
Historical Reliability
Current Disruptions
Cargo Constraints

Example Recommendation

RECOMMENDED ROUTE: C

✓ Lower disruption probability
✓ Better accessibility
✓ Lower predicted delay
✓ Higher reliability

---

🛣️ 4. Accessibility Intelligence

Every route receives an accessibility score.

Example

Accessibility Score: 78 / 100

Road Quality        82
Weather Risk        70
Traffic             81
Terrain Difficulty  61
Connectivity        92
Infrastructure      78

Overall              78

The accessibility engine considers:

- Road quality
- Terrain difficulty
- Weather conditions
- Traffic
- Connectivity
- Infrastructure
- Historical reliability
- Disruption frequency

---

⚠️ 5. Disruption Intelligence

The system tracks events that can affect logistics routes.

Supported Disruptions

FLOOD
LANDSLIDE
ROAD_CLOSURE
ACCIDENT
WEATHER
TRAFFIC
INFRASTRUCTURE
OTHER

Each disruption contains:

Type
Severity
Location
Affected Routes
Description
Start Time
Expected End Time
Source
Status

---

📍 6. Real-Time Shipment Tracking

Tracking architecture:

Shipment
    ↓
Vehicle
    ↓
GPS Location
    ↓
Backend
    ↓
Socket.IO
    ↓
React Map

Tracking data:

Shipment ID
Vehicle ID
Latitude
Longitude
Speed
Heading
Timestamp

WebSocket Events

shipment:location
shipment:status
shipment:delay
shipment:alert

---

🤖 7. AI / ML Intelligence

AI is focused on prediction, risk assessment, and decision support.

AI Capabilities

1. ETA Prediction
2. Delay Prediction
3. Route Risk Prediction
4. Route Recommendation
5. Accessibility Scoring
6. Disruption Impact Prediction
7. Alternative Route Recommendation

---

🔬 AI Pipeline

Historical Shipment Data
          +
Weather Data
          +
Road Conditions
          +
Traffic
          +
Terrain
          +
Infrastructure
          +
Disruption History
          ↓
   Feature Engineering
          ↓
       ML Models
          ↓
 ┌────────┼──────────┐
 ↓        ↓          ↓
ETA      Risk   Accessibility
 ↓        ↓          ↓
 └────────┼──────────┘
          ↓
   Route Optimization
          ↓
   AI Recommendation

---

📊 Example AI Prediction

Input

Origin: Guwahati
Destination: Imphal

Weather: Heavy Rain
Traffic: High
Road Status: Partially Blocked
Terrain: Difficult
Historical Delay Rate: 34%

Output

Risk Score: 82%

Predicted Delay:
+4.7 hours

Recommendation:
Use Alternative Route B

Reason:
Route B has lower predicted delay
and lower disruption exposure.

---

🚛 8. Vehicle Management

Vehicle information:

Vehicle Number
Type
Capacity
Current Location
Status
Driver
Fuel Type

Vehicle statuses:

AVAILABLE
ASSIGNED
IN_TRANSIT
MAINTENANCE
OFFLINE

---

👨‍✈️ 9. Driver Management

Driver information:

Name
Phone
License Number
Vehicle
Status
Experience

---

🏗️ 10. Infrastructure Intelligence

The platform maintains information about:

Roads
Bridges
Railways
Airports
Ports
Warehouses
Checkpoints
Fuel Stations
Logistics Hubs

Infrastructure data:

Name
Type
Location
Capacity
Status
Accessibility Score
Last Updated

---

📈 11. Analytics

The analytics system provides:

Total Shipments
Delivered %
Delayed %
Average ETA
Average Delay
Route Reliability
Fuel Efficiency
Regional Accessibility
Disruption Frequency
Transport Mode Distribution

Regional Analytics

The system can identify:

- High-risk regions
- Low-accessibility regions
- Frequently disrupted routes
- Delay-prone corridors
- Infrastructure gaps
- Transportation bottlenecks

---

🔔 12. Intelligent Alerts

Alerts can be generated automatically.

Alert Types

ROUTE_BLOCKED
DELAY_RISK
WEATHER_WARNING
SHIPMENT_DELAY
ETA_CHANGE
VEHICLE_ISSUE

Example:

⚠️ WEATHER WARNING

Heavy rainfall detected near Route A.

Shipment SH1023:
Risk: 31% → 72%
ETA: 13 hrs → 17 hrs

Alternative Route B available.

---

🔎 13. Global Search

Search across:

Shipments
Vehicles
Drivers
Routes
Disruptions
Infrastructure

Example:

GET /api/search?q=SH1023

---

🏗️ System Architecture

                         NEXUS-NER
                             │
            ┌────────────────┼────────────────┐
            │                │                │
        SHIPMENTS          ROUTES          TRACKING
            │                │                │
            └────────────┬───┴───────┬────────┘
                         │           │
                 AI INTELLIGENCE  DISRUPTIONS
                         │           │
                         └─────┬─────┘
                               │
                       ACCESSIBILITY
                               │
                    ┌──────────▼──────────┐
                    │  LOGISTICS ENGINE   │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
          MongoDB            Redis             AI/ML
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                        React Frontend

---

💻 Technology Stack

Frontend

React
React Router
Zustand / Context API
React Query
Axios
Socket.IO Client
Maps
Charts

Backend

Node.js
Express.js
REST API
Socket.IO
JWT
RBAC

Database

MongoDB
Mongoose

Performance

Redis
BullMQ
Background Workers

AI / ML

Python
Pandas
NumPy
Scikit-learn
XGBoost / LightGBM
FastAPI

---

📁 Project Structure

NEXUS-NER/

├── client/
│
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── store/
│   │   ├── api/
│   │   ├── utils/
│   │   └── App.jsx
│   │
│   └── package.json
│
├── server/
│
│   ├── src/
│   │
│   ├── config/
│   │   ├── database.js
│   │   └── redis.js
│   │
│   ├── models/
│   │   ├── User.js
│   │   ├── Shipment.js
│   │   ├── Vehicle.js
│   │   ├── Driver.js
│   │   ├── Route.js
│   │   ├── Tracking.js
│   │   ├── Disruption.js
│   │   ├── Infrastructure.js
│   │   └── Alert.js
│   │
│   ├── controllers/
│   ├── services/
│   ├── routes/
│   ├── middleware/
│   ├── utils/
│   ├── app.js
│   └── server.js
│
├── ai/
│
│   ├── data/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── prediction/
│   ├── recommendation/
│   ├── training/
│   └── api/
│
├── docs/
│
├── .env.example
├── docker-compose.yml
└── README.md

---

🔌 API Architecture

Authentication

POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/refresh

Shipments

POST   /api/shipments
GET    /api/shipments
GET    /api/shipments/:id
PATCH  /api/shipments/:id
DELETE /api/shipments/:id

GET   /api/shipments/search
PATCH /api/shipments/:id/status
PATCH /api/shipments/:id/vehicle
PATCH /api/shipments/:id/route

Routes

POST /api/routes/calculate
POST /api/routes/compare
POST /api/routes/optimize

GET /api/routes/:id
GET /api/routes/:id/risk
GET /api/routes/history
GET /api/routes/:id/disruptions

Tracking

POST /api/tracking/location
GET  /api/tracking/:shipmentId
GET  /api/tracking/:shipmentId/history

Vehicles

POST   /api/vehicles
GET    /api/vehicles
GET    /api/vehicles/:id
PATCH  /api/vehicles/:id
DELETE /api/vehicles/:id
GET    /api/vehicles/available

Drivers

POST   /api/drivers
GET    /api/drivers
GET    /api/drivers/:id
PATCH  /api/drivers/:id
DELETE /api/drivers/:id

Disruptions

POST   /api/disruptions
GET    /api/disruptions
GET    /api/disruptions/:id
PATCH  /api/disruptions/:id
DELETE /api/disruptions/:id

GET /api/disruptions/nearby
GET /api/routes/:id/disruptions

Infrastructure

POST   /api/infrastructure
GET    /api/infrastructure
GET    /api/infrastructure/:id
PATCH  /api/infrastructure/:id
DELETE /api/infrastructure/:id

GET /api/infrastructure/nearby

AI

POST /api/ai/predict-eta
POST /api/ai/predict-delay
POST /api/ai/risk-score
POST /api/ai/accessibility-score
POST /api/ai/route-recommendation
POST /api/ai/disruption-impact

Analytics

GET /api/analytics/overview
GET /api/analytics/shipments
GET /api/analytics/routes
GET /api/analytics/delays
GET /api/analytics/regions
GET /api/analytics/disruptions

Alerts

GET   /api/alerts
PATCH /api/alerts/:id/read
PATCH /api/alerts/read-all

---

⚡ Performance Architecture

All large collections must support:

Pagination
Filtering
Sorting
Searching
Caching

Example:

GET /api/shipments
?page=1
&limit=20
&status=IN_TRANSIT
&priority=HIGH
&sort=riskScore
&order=desc

Response:

{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 348,
    "totalPages": 18,
    "hasNext": true,
    "hasPrevious": false
  }
}

---

⚡ Redis & Background Processing

Redis will be used for:

Route calculations
Dashboard metrics
Active disruptions
Regional statistics
Accessibility calculations

BullMQ will handle:

ETA recalculation
Risk calculation
Disruption processing
Analytics aggregation
Alert generation
Accessibility recalculation

Example:

Weather Update
      ↓
Disruption Detected
      ↓
Background Job
      ↓
Affected Routes
      ↓
Shipment Risk
      ↓
Delay Prediction
      ↓
Alert
      ↓
Alternative Route

---

🧩 Frontend Architecture

Component
    ↓
Custom Hook
    ↓
State / Query Cache
    ↓
API Service
    ↓
Backend

State

AuthState
ShipmentState
RouteState
TrackingState
AlertState
DashboardState

Hooks

useAuth()

useShipments()
useShipment()

useCreateShipment()
useUpdateShipment()

useRoutes()
useRouteOptimization()

useTracking()

useDisruptions()

useVehicles()

useDrivers()

useInfrastructure()

useAlerts()

useAnalytics()

---

🧪 MVP

The first version should focus on one complete end-to-end logistics workflow.

LOGIN
  ↓
DASHBOARD
  ↓
CREATE SHIPMENT
  ↓
ORIGIN / DESTINATION
  ↓
GENERATE ROUTES
  ↓
ACCESSIBILITY SCORE
  ↓
RISK CALCULATION
  ↓
SELECT BEST ROUTE
  ↓
TRACK SHIPMENT
  ↓
DISRUPTION
  ↓
RISK RECALCULATION
  ↓
DELAY PREDICTION
  ↓
ALTERNATIVE ROUTE
  ↓
ALERT

---

🏆 SIH Demo Scenario

The strongest demonstration should revolve around one shipment.

Step 1 — Create Shipment

Origin: Guwahati
Destination: Imphal

Cargo: Essential Goods
Weight: 10,000 kg
Priority: HIGH
Transport: ROAD

Step 2 — Generate Routes

Route A
Route B
Route C

Step 3 — AI Recommendation

Recommended Route: A

Risk: 31%
ETA: 13 hours
Accessibility: High

Step 4 — Simulate Disruption

⚠️ Severe Rainfall Detected

Risk:
31% → 72%

ETA:
13 hrs → 17 hrs

Step 5 — AI Response

Alternative Route Available

Route B

Risk Reduction: 38%
Expected Delay Reduction: 3.4 hrs

Recommendation:
REROUTE SHIPMENT

Step 6 — Operator Accepts

Operator
    ↓
Accept Recommendation
    ↓
Route Updated
    ↓
Map Updated
    ↓
Shipment Continues

This demonstrates the core value of NEXUS-NER:

«The system doesn't just display information. It detects changing conditions and recommends what the logistics operator should do.»

---

🗺️ Development Roadmap

Phase 1 — Foundation

- [ ] Project setup
- [ ] MongoDB connection
- [ ] Authentication
- [ ] JWT
- [ ] Roles & permissions
- [ ] User model
- [ ] Shipment model
- [ ] Shipment CRUD
- [ ] API contract

---

Phase 2 — Logistics Core

- [ ] Vehicle management
- [ ] Driver management
- [ ] Route model
- [ ] Shipment assignment
- [ ] Route generation
- [ ] Route comparison
- [ ] Route optimization

---

Phase 3 — Tracking

- [ ] Map integration
- [ ] Vehicle location
- [ ] Shipment tracking
- [ ] Tracking history
- [ ] Socket.IO
- [ ] Real-time updates

---

Phase 4 — Disruption Intelligence

- [ ] Disruption model
- [ ] Weather integration
- [ ] Road disruption data
- [ ] Accessibility scoring
- [ ] Risk calculation
- [ ] Alert system
- [ ] Alternative route logic

---

Phase 5 — AI / ML

- [ ] Dataset preparation
- [ ] Data preprocessing
- [ ] Feature engineering
- [ ] ETA model
- [ ] Delay prediction
- [ ] Risk prediction
- [ ] Accessibility model
- [ ] Route recommendation
- [ ] Disruption impact prediction

---

Phase 6 — Scale & Analytics

- [ ] Analytics dashboard
- [ ] Regional analytics
- [ ] Redis caching
- [ ] BullMQ
- [ ] Background workers
- [ ] Performance optimization
- [ ] Logging
- [ ] Monitoring

---

🚫 What We Will NOT Build Initially

To maintain focus and meet the SIH timeline:

❌ Generic chatbot
❌ Blockchain
❌ Microservices
❌ Mobile application
❌ Complex deep-learning architecture
❌ Huge admin panel
❌ Unnecessary CRUD modules
❌ Dozens of disconnected dashboards

The priority is:

LOGISTICS ENGINE
      ↓
AI INTELLIGENCE
      ↓
REAL-TIME RESPONSE
      ↓
VISUALIZATION

---

🎯 Priority Levels

P0 — MUST HAVE

Authentication
Shipment Management
Route Generation
Accessibility Score
Risk Calculation
Disruption Detection
AI Recommendation
Basic Tracking
Alerts

P1 — HIGH VALUE

ETA Prediction
Delay Prediction
Alternative Route Recommendation
Regional Analytics
Live WebSocket Tracking

P2 — POLISH

Redis
BullMQ
Advanced Analytics
Infrastructure Intelligence
Advanced Filtering
Global Search

P3 — OPTIONAL

Advanced AI
Additional Transport Modes
Advanced Government Dashboard
Mobile Application
Advanced Automation

---

📐 Engineering Principles

API First

Freeze the API contract before building the complete UI.

Modular Architecture

Keep:

Controllers
Services
Models
Routes
Middleware
AI

separated.

Explainable AI

Every recommendation should provide understandable reasoning.

Example:

Recommended Route B

Why?

✓ 28% lower predicted delay
✓ 17% lower disruption risk
✓ Better accessibility
✓ Higher historical reliability

Real-Time Where It Matters

Use WebSockets for:

Location
Shipment Status
Alerts
ETA Changes
Disruptions

Performance by Design

Use:

Pagination
Indexes
Caching
Redis
Background Jobs
Lazy Loading

---

📊 Success Criteria

NEXUS-NER should successfully demonstrate:

- [x] Shipment creation
- [x] Route generation
- [x] Route comparison
- [x] Accessibility scoring
- [x] Risk calculation
- [x] Disruption detection
- [x] ETA prediction
- [x] Delay prediction
- [x] Alternative route recommendation
- [x] Shipment tracking
- [x] Intelligent alerts
- [x] Regional analytics

Most Important Success Criterion

The system must demonstrate:

REAL-WORLD CONDITION CHANGES
            ↓
      SYSTEM DETECTS IT
            ↓
       RISK CHANGES
            ↓
       ETA CHANGES
            ↓
   AI RECOMMENDS ACTION
            ↓
      OPERATOR ACTS
            ↓
       ROUTE UPDATES

---

🚀 Final Vision

NEXUS-NER evolves logistics management from:

Traditional Logistics Dashboard

into:

AI-Powered Logistics Decision Support System

The platform continuously answers:

Where is the shipment?
        ↓
What is happening on the route?
        ↓
How accessible is the route?
        ↓
What risks are emerging?
        ↓
How much delay is expected?
        ↓
What should the operator do?
        ↓
Which alternative is better?

---

🏆 NEXUS-NER

See the Route. Predict the Risk. Move Smarter.

«Built for Smart India Hackathon 2026 — SIH26002

AI • Logistics • Accessibility • Resilience • Real-Time Intelligence»