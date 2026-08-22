# 🛡️ SafeWalk v2.0
> **"Google Maps shows the fastest route. SafeWalk shows the safest route — for any city worldwide, updated in real-time by women themselves."**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini%20AI-orange.svg)](https://deepmind.google/technologies/gemini/)
[![RAG Architecture](https://img.shields.io/badge/RAG-WHO%20%26%20NCRB%20Grounded-green.svg)]()
[![OpenStreetMap / OSRM](https://img.shields.io/badge/Navigation-OSRM%20%2B%20Overpass-brightgreen.svg)]()
[![Streamlit UI](https://img.shields.io/badge/Frontend-Streamlit%20%2B%20Folium-red.svg)]()
[![Security Hardened](https://img.shields.io/badge/Security-OWASP%20Hardened-success.svg)]()

---

## 📌 1. Executive Summary

Traditional navigation apps prioritize speed ($m/min$) over human safety. For women walking alone—especially at night or in unfamiliar cities—the fastest route is often through unlit alleys or poorly monitored areas.

**SafeWalk v2.0** solves this by introducing **Dual-Route Safety Optimization**:
- 🟢 **Safest Route**: Calculated using real road geometry (OSRM), streetlight coverage, POI density, police proximity, and real-time community report weights.
- 🔴 **Fastest Route**: The standard shortest-time path, highlighted alongside danger zone markers.

Powered by **Google Gemini AI** and **RAG Knowledge Base (WHO & NCRB Guidelines)**, SafeWalk converts raw navigation into actionable, AI-guided safety briefings tailored to the user's journey.

---

## 🏗️ 2. System Architecture & Workflow

```text
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
   - **Time of Day Penalty:** Continuous time curve (up to -30 penalty at 02:00 AM).
   - **Weighted Incidents:** Sum of active incident weights x severities near the route.
   - **Streetlights:** +0 for lit streets, -20 for unlit streets.
   - **POI Density:** High shop/amenity density adds up to +15 bonus.
   - **Police Proximity:** Police stations within 800m add +10 bonus.
   - Sorts routes so `routes[0]` is the **Safest Route** (Green) and `routes[-1]` is the **Fastest Route** (Red/Dashed).
4. **Natural Language Reporting & Decay Flywheel:**
   When a user reports an incident in plain text, `genai_layer.process_incident_report()` uses Gemini NLP to extract structured JSON. The incident is saved into SQLite (`safewalk.db`) and `report_manager.update_all_weights()` recalculates incident weights using the 48-hour half-life decay formula:
   ```text
   Weight = e^(-0.693 * hours_ago / 48) * Trust_Modifier * Verified_Bonus
   ```
5. **AI News & Open Data Ingestion:**
   `news_incident_fetcher.py` queries Gemini AI with Search Grounding to fetch recent news reports, police advisories, and NCRB crime data for the active city, geocodes them, and ingests them into `safewalk.db`.
6. **RAG-Grounded AI Safety Briefing:**
   `rag_knowledge.py` retrieves matching WHO/NCRB guidelines and injects them alongside route scores and live report counts into `genai_layer.generate_safety_briefing()` to produce a 5-bullet safety briefing.

---

## 📁 3. Project Directory Structure

```text
SafeWalk/
│
├── ai_backend/                       # AI & RAG Layer
│   ├── genai_layer.py                # Gemini AI: Safety Briefings, Incident NLP, SOS SMS
│   ├── news_incident_fetcher.py       # AI News Ingestion: Fetch news alerts & NCRB data
│   └── rag_knowledge.py               # RAG Engine: WHO Guidelines + NCRB Insights vector store
│
├── backend/                          # Core Navigation & Database Engine
│   ├── safewalk_service.py            # Master Unified Integration API
│   ├── geocoder.py                    # High-Precision Multi-Stage Geocoder & Landmark Database
│   ├── osm_safety_data.py             # Overpass API (Streetlights, POIs, Police, Alleys)
│   ├── router.py                      # HTTPS OSRM Foot Router & Real Road Geometry Engine
│   ├── safety_scorer.py               # Multi-factor Safety Scoring Engine (0-100)
│   ├── report_manager.py              # Dynamic Weight Decay & Community Voting Engine
│   ├── setup_db.py                    # SQLite Database Schema & Seed Data
│   ├── cli_demo.py                    # Interactive Terminal CLI Application
│   ├── test_integration.py            # End-to-End System Integration Test Suite
│   ├── test_m2_backend.py             # Backend Core Unit Test Suite
│   └── safewalk.db                    # SQLite Production Database
│
├── frontend/                         # Streamlit Dashboard UI Layer
│   ├── app.py                         # Streamlit Web App (Folium map, live feed, SOS, city search)
│   ├── map_builder.py                 # Folium Map Builder (HeatMap, real road polylines, danger markers)
│   └── requirements.txt               # Frontend Dependencies
│
├── .streamlit/                       # Streamlit Theme Configuration
│   └── config.toml                    # Light theme tokens & typography settings
│
├── .env                              # Environment Variables (GEMINI_API_KEY)
├── requirements.txt                  # Python Dependencies
└── README.md                         # Project Documentation
```

---

## ⚡ 4. Setup & Deployment Guide

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

Launch the Streamlit web interface locally:

```bash
streamlit run frontend/app.py
```

---

### 3️⃣ Streamlit Community Cloud Deployment (100% Free)

SafeWalk is pre-configured for instant 1-click deployment on **Streamlit Community Cloud**:

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
2. Click **New app** → Select repository `vr11-ai/SafeWalk` (branch `main`).
3. Set **Main file path** to `frontend/app.py`.
4. Under **Advanced settings...** → **Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   ```
5. Click **Deploy!**

---

### 4️⃣ Running the Interactive Terminal Application (CLI)

To test all SafeWalk features interactively in your terminal:

```bash
python backend/cli_demo.py
```

---

### 5️⃣ Running Test Suites

#### Run Backend Unit Tests:
```bash
python backend/test_m2_backend.py
```

#### Run End-to-End Integration Tests:
```bash
python backend/test_integration.py
```

---

## 🏆 5. Key Differentiators & Judge Talking Points

| Feature | Competitors (Google Maps, Waze) | SafeWalk v2.0 |
| :--- | :--- | :--- |
| **Route Optimization** | Purely fastest time ($m/min$) | Dual Routes: **Safest** (0-100) vs **Fastest** |
| **Route Geometry** | Basic line path | **100% Real Pedestrian Road Geometry (OSRM)** |
| **Spatial Precision** | Standard city search | **110-Meter Fine-Grained Grid Caching** |
| **Geocoding Accuracy** | Standard address lookup | **Multi-Stage Landmark Table & Precision Bounds** |
| **Incident Decay** | Static or binary flags | Exponential decay curve (48h half-life) |
| **Reporting Interface** | Multi-step manual forms | Natural Language text (English/Hindi) via Gemini NLP |
| **AI News Ingestion** | None | Real-time news alerts & NCRB crime ingestion |
| **AI Safety Guidance** | None | 5-bullet briefing grounded in WHO/NCRB RAG context |
| **Community Trust** | Unverified user reports | 3+ upvote verification badge & 1.3x weight boost |
| **Global Scale** | Limited to partnered cities | Global support for any city via OpenStreetMap & Nominatim |

---

## 🚀 6. Future Roadmap & Strategic Vision

- **Dedicated HTML5 / CSS3 / JavaScript Custom Frontend**: Future migration to a standalone custom web stack SPA with interactive Leaflet map rendering and mobile PWA support.
- **IoT Smartwatch & Wearable Panic Integration**: One-touch panic trigger on Apple Watch / WearOS for instant emergency location broadcasts.
- **Real-Time Voice Navigation**: Spoken turn-by-turn guidance focusing on well-lit main arterial roads and nearby commercial nodes.
- **24/7 Verified Safe Haven Partner Network**: Partnering with verified pharmacies, 24/7 convenience stores, and police booths as designated emergency walk-in shelters.

---

## 👥 7. Team Credits & Roles

SafeWalk v2.0 was designed and developed by **Team SafeWalk** (UPES Dehradun, 2026):

- **Vidit Raturi** — **Team Lead**  
  *Full-Stack System Integration, End-to-End Feature Development, OWASP Security Hardening, Dynamic Decay Weight Engine, High-Precision Multi-Stage Geocoding, and Bug Resolution.*
- **Vanshika** — **Frontend Lead**  
  *Streamlit Dashboard UI/UX, Folium Map Component Architecture, Live Incident Feed Components, and SOS Interface.*
- **Ritika** — **Backend Foundation Lead**  
  *SQLite Database Schema Architecture, Initial OSRM & Overpass API Routing Foundation, and Core Safety Scoring Base.*

---

## 📜 8. License & Credits

Built with ❤️ by **Team SafeWalk** (UPES Dehradun, 2026).  
Powered by **Google Gemini AI**, **OpenStreetMap**, **OSRM**, **ReportLab**, and **Streamlit**.
