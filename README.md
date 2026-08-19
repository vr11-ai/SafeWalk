# 🛡️ SafeWalk v2.0
> **"Google Maps shows the fastest route. SafeWalk shows the safest route — for any city worldwide, updated in real-time by women themselves."**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Gemini 1.5 Flash](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![RAG Architecture](https://img.shields.io/badge/RAG-WHO%20%26%20NCRB%20Grounded-green.svg)]()
[![OpenStreetMap / OSRM](https://img.shields.io/badge/Navigation-OSRM%20%2B%20Overpass-brightgreen.svg)]()
[![Security Hardened](https://img.shields.io/badge/Security-OWASP%20Hardened-success.svg)]()

---

## 📌 1. Project Overview

**SafeWalk** is an AI-powered real-time women's safety navigation network and risk briefing system. While conventional navigation platforms optimize purely for travel duration, SafeWalk evaluates pedestrian routes across **6 critical safety dimensions**—combining live crowdsourced reports, OpenStreetMap infrastructural data (streetlights, POIs, police proximity), real-time AI news alerts, and WHO/NCRB grounded RAG AI briefings.

### 🌟 Key Features & Latest Architectural Upgrades
- **Global Custom City Support:** Works seamlessly for **ANY city worldwide** (Dehradun, Delhi, Mumbai, Bengaluru, Tokyo, London, Paris, NYC, Sydney) with auto-geocoding and instant map re-centering.
- **High-Precision Multi-Stage Geocoding:** Custom local landmark database (Chowks, Colleges, Metro Exits, Malls) combined with suffix cleaning and Nominatim search for 100% exact GPS coordinates.
- **100% Real Pedestrian Road Geometry:** HTTPS OSRM foot router yields **280 to 650+ precise street points** following actual roads, sidewalks, footpaths, and turns (zero straight lines!).
- **110-Meter Fine-Grained Spatial Cache Grid:** OpenStreetMap safety evaluation runs on a fine **110-meter spatial grid** (`round(lat, 3), round(lng, 3)`), ensuring every street corner, unlit alley, and main road receives unique, highly dynamic safety scores.
- **Continuous Sinusoidal Daylight Curve:** Replaced discrete step functions with a smooth mathematical daylight curve ($\cos(	ext{hour})$), continuously scaling time penalties from $0$ points at peak daylight ($14:00$) to $-30$ points at peak darkness ($02:00	ext{ AM}$).
- **Real-Time Recency Decay Flywheel:** Incidents carry maximum weight ($1.0$) when fresh and automatically decay over time ($48$-hour half-life exponential curve), keeping the map sensitive to immediate risks.
- **Natural Language Incident Reporting:** Women report harassment or unsafe areas in plain English or Hindi without complex forms—Gemini NLP extracts structured details automatically.
- **AI News & NCRB Crime Alert Ingester:** Gemini AI + Search Grounding fetches live news reports, police advisories, and NCRB crime data for the active city and ingests them into the live safety map.
- **RAG-Grounded Safety Briefings:** Generates tailored 5-bullet route advisories grounded in official **WHO Safety Directives** and **NCRB Analytical Insights**.
- **Community Upvoting & Verification:** $3+$ community upvotes award a **✔ Verified Badge** and apply a $1.3x$ trust weight multiplier to high-risk zones.
- **Security Hardened (OWASP Protection):** Full HTML XSS escaping via `html.escape()`, API key validation, prompt injection `<USER_REPORT>` XML boundary tags, and thread-safe SQLite context managers.

---

## 🎨 2. Frontend User Interface & Experience (`frontend/`)

The SafeWalk frontend is built using **Streamlit** integrated with **Folium / Leaflet.js** for high-performance interactive mapping, wrapped in a sleek **Dark Mode Design System** (`#0e1117` background with `#00F2FE` gradient accents).

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                               SAFEWALK FRONTEND ARCHITECTURE                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
  [Sidebar Control Panel]                 [Main Interface Tabs]
  ├─ Active City Selector                 ├─ 🗺️ Tab 1: Safe Route Finder & Folium Map
  ├─ Travel Time Slider (0-23h)           ├─ 📢 Tab 2: Natural Language Incident Report
  ├─ 📰 Fetch AI News Button              ├─ 🔥 Tab 3: Live Community Feed & Upvoting
  └─ 🌐 City Safety Overview              └─ 🧠 Tab 4: RAG Safety Assistant & Emergency SOS
```

### 🖥️ Frontend Modules & Features Breakdown:

#### 1. 🗺️ Tab 1: Safe Route Finder & Interactive Map
- **Location Input Bar:** Single clean input row with quick 1-click landmark suggestion chips (`📌 Clock Tower`, `📌 UPES Bidholi`, `📌 Pacific Mall`). Supports typing any custom address directly.
- **CartoDB Dark Matter Folium Map:**
  - 🟢 **Safest Route Polyline:** Drawn in vibrant Emerald Green (`#10B981`, weight 6) with safety score tooltips out of 100.
  - 🔴 **Fastest Route Polyline:** Drawn in Dashed Red (`#EF4444`, weight 4) for instant visual comparison.
  - Start (`▶` Green) and Destination (`🚩` Blue) pin markers.
  - Red pulse Danger Zone circles ($<50$ safety score).
  - Recency Decay HeatMap overlay ($0.05-1.0$ weight gradient).
- **Route Metrics Panel:** Displays Safety Score badge, Walk Time duration, Danger Zone count, and Extra Time detour penalty.
- **🤖 AI Route Safety Briefing:** Real-time 5-bullet route guidance powered by Gemini Flash + WHO/NCRB knowledge.

#### 2. 📢 Tab 2: Natural Language Incident Reporting
- **Free-Text Incident Area:** Women report incidents in plain English or Hindi (e.g. *"Catcalling and aggressive shouting near HKV parking lot at 10pm"*).
- **Gemini NLP Extraction:** Parses structured JSON (`location_description`, `incident_type`, `severity`, `time_of_day`) automatically without manual forms.
- **Instant Weight Recalculation:** Submitting a report triggers balloons 🎉, updates SQLite DB, and recalculates recency weights immediately.

#### 3. 🔥 Tab 3: Live Community Feed & Upvoting
- **City Metrics Bar:** Displays Total Reports, Last 24 Hours count, Verified Reports count, and Average Severity ($1-3$).
- **Live Feed Cards:** Real-time report cards with time-ago indicators (`🕒 15m ago`, `🕒 2h ago`), severity color icons, and source tags.
- **👍 Upvote / 👎 Downvote Buttons:** Session-based voting deduplication. Reports receiving $3+$ community upvotes automatically earn a **✔ Verified Badge** and receive a $1.3x$ weight boost.

#### 4. 🧠 Tab 4: RAG AI Safety Assistant & Emergency SOS
- **RAG Q&A Assistant:** Users ask any women's safety question (e.g. *"What should I do if I feel followed at night?"*) and receive guidance grounded in WHO & NCRB guidelines, with an expandable retrieved context viewer.
- **Emergency SOS SMS Generator:** Generates a formatted 160-character emergency SMS containing the user's name, current location, destination, and urgent call to action.

---

## 🔄 3. How It Works (System Workflow & Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SAFEWALK WORKFLOW                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
   [User Input]          [Location & Route Engine]              [Safety Scoring Engine]
 Start & Destination  ──► Multi-Stage High-Precision Geocoder  ──► HTTPS OSRM Foot Walking Routes
                         └─► Overpass API Safety Data          ├─► Streetlight Coverage
                             (Police, Lights, POIs)            ├─► Weighted Incident Decay
                                                               └─► Dark Alley Penalties
                                                                          │
                                                                          ▼
   [AI & RAG Layer]            [Community & News Flywheel]       [Dual Route Output]
 RAG WHO/NCRB Engine  ◄─── Real-Time Incident Persistence  ◄─── 🟢 Safest Route (Score: 84)
 Gemini Flash Briefing     ├─► Gemini NLP Text Parser          🔴 Fastest Route (Score: 52)
 5-Bullet Guidance         ├─► AI News & Alert Ingestor        📍 Danger Zone Markers
                           └─► 3+ Vote Community Verification
```

### Step-by-Step Execution Flow:
1. **High-Precision Geocoding & City Detection:**
   `geocoder.geocode_address()` converts location inputs (e.g. *"Clock Tower"*, *"UPES Bidholi"*, *"Ballupur Chowk"*) to exact `(lat, lng)` coordinates using multi-stage local landmark tables and structured Nominatim searches.
2. **OSRM Real Road Geometry Generation:**
   `router.get_alternative_routes()` queries HTTPS OSRM endpoints (`https://router.project-osrm.org/route/v1/foot`) to fetch candidate walking paths containing up to 650+ pedestrian street points following actual roads and turns.
3. **Multi-Factor Safety Scoring (0 - 100):**
   `safety_scorer.calculate_safety_score()` evaluates coordinates along each route:
   - **Continuous Time of Day Penalty:** Smooth sinusoidal curve (up to $-30$ penalty at 02:00 AM).
   - **Weighted Incidents:** Sum of active incident weights x severities near the route.
   - **Streetlights:** $+0$ for lit streets, $-20$ for unlit streets.
   - **POI Density:** High shop/amenity density adds up to $+15$ bonus.
   - **Police Proximity:** Police stations within $800	ext{m}$ add $+10$ bonus.
   - Sorts routes so `routes[0]` is the **Safest Route** (Green) and `routes[-1]` is the **Fastest Route** (Red/Dashed).
4. **Natural Language Reporting & Decay Flywheel:**
   When a user reports an incident in plain text, `genai_layer.process_incident_report()` uses Gemini NLP to extract structured JSON. The incident is saved into SQLite (`safewalk.db`) and `report_manager.update_all_weights()` recalculates all incident weights using the 48-hour half-life decay formula:
   ```text
   Weight = e^(-0.693 * hours_ago / 48) * Trust_Modifier * Verified_Bonus
   ```
5. **AI News & Open Data Ingestion:**
   `news_incident_fetcher.py` queries Gemini AI with Search Grounding to fetch recent news reports, police advisories, and NCRB crime data for the active city, geocodes them, and ingests them into `safewalk.db`.
6. **RAG-Grounded AI Safety Briefing:**
   `rag_knowledge.py` retrieves matching WHO/NCRB guidelines and injects them alongside route scores and live report counts into `genai_layer.generate_safety_briefing()` to produce a 5-bullet safety briefing.

---

## 📁 4. Project Directory Structure

```text
SafeWalk/
│
├── ai_backend/                       # AI & RAG Layer
│   ├── genai_layer.py                # Gemini AI: Briefings, Incident NLP, SOS SMS
│   ├── news_incident_fetcher.py       # AI News Ingestion: News alerts & NCRB data fetcher
│   └── rag_knowledge.py               # RAG Engine: WHO Guidelines + NCRB Insights vector store
│
├── backend/                          # Core Navigation & Database Engine
│   ├── safewalk_service.py            # Master Unified Integration API
│   ├── geocoder.py                    # High-Precision Multi-Stage Geocoder & Landmark Database
│   ├── osm_safety_data.py             # Overpass API (Streetlights, POIs, Police, Alleys)
│   ├── router.py                      # HTTPS OSRM Foot Router & Real Road Geometry Engine
│   ├── safety_scorer.py               # Multi-factor Safety Scoring Engine (0-100)
│   ├── report_manager.py              # Dynamic Weight Decay & Community Voting Engine
│   ├── setup_db.py                    # SQLite Database Schema & Delhi Demo Seed Data
│   ├── cli_demo.py                    # Interactive Terminal CLI Application
│   ├── test_integration.py            # End-to-End System Integration Test Suite
│   ├── test_m2_backend.py             # Backend Core Unit Test Suite
│   └── safewalk.db                    # SQLite Production Database
│
├── frontend/                         # User Interface Layer (Streamlit)
│   ├── app.py                         # Streamlit Web App (Folium dark map, live feed, SOS, city search)
│   ├── map_builder.py                 # Folium Map Builder (HeatMap, real road polylines, danger markers)
│   └── requirements.txt               # Frontend Dependencies
│
├── .env                              # Environment Variables (GEMINI_API_KEY)
├── requirements.txt                  # Project Python Dependencies
└── README.md                         # Project Documentation
```

---

## ⚡ 5. Setup & Running Guide

### 1️⃣ Installation & Environment Setup
Clone the repository and install the dependencies:

```bash
git clone https://github.com/vr11-ai/SafeWalk.git
cd SafeWalk
pip install -r requirements.txt
```

Set your **Gemini API Key** in `.env`:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

---

### 2️⃣ Running the Streamlit Web Application

Launch the web interface:

```bash
streamlit run frontend/app.py
```

---

### 3️⃣ Running the Interactive Terminal Application (CLI)

To test all SafeWalk features interactively in your terminal:

```bash
python backend/cli_demo.py
```

---

### 4️⃣ Running Test Suites

#### Run Backend Unit Tests:
```bash
python backend/test_m2_backend.py
```

#### Run End-to-End Integration Tests:
```bash
python backend/test_integration.py
```

---

## 🏆 6. Key Differentiators & Judge Talking Points

| Feature | Competitors (Google Maps, Waze) | SafeWalk v2.0 |
| :--- | :--- | :--- |
| **Route Optimization** | Purely fastest time ($m/min$) | Dual Routes: **Safest** ($0-100$) vs **Fastest** |
| **Route Geometry** | Basic line path | **100% Real Pedestrian Road Geometry (OSRM)** |
| **Spatial Precision** | Standard city search | **110-Meter Fine-Grained Grid Caching** |
| **Geocoding Accuracy** | Standard address lookup | **Multi-Stage Landmark Table & Precision Bounds** |
| **Incident Decay** | Static or binary flags | Exponential decay curve ($48	ext{h}$ half-life) |
| **Reporting Interface** | Multi-step manual forms | Natural Language text (English/Hindi) via Gemini NLP |
| **Security Hardening** | Standard web security | **XSS Escaping, Prompt Injection Tags, Thread-Safe DB** |
| **AI Safety Guidance** | None | 5-bullet briefing grounded in WHO/NCRB RAG context |
| **Community Trust** | Unverified user reports | 3+ upvote verification badge & $1.3x$ weight boost |
| **Global Scale** | Limited to partnered cities | Global support for any city via OpenStreetMap & Nominatim |

---

## 📜 7. License & Credits

Built with ❤️ by **Team SafeWalk** (UPES Dehradun, 2026).  
Powered by **Google Gemini AI**, **OpenStreetMap**, **OSRM**, **ReportLab**, and **Streamlit**.
