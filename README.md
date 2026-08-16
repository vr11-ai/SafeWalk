# 🛡️ SafeWalk v2.0
> **"Google Maps shows the fastest route. SafeWalk shows the safest route — for any city worldwide, updated in real-time by women themselves."**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Gemini 1.5 Flash](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![RAG Architecture](https://img.shields.io/badge/RAG-WHO%20%26%20NCRB%20Grounded-green.svg)]()
[![OpenStreetMap / OSRM](https://img.shields.io/badge/Navigation-OSRM%20%2B%20Overpass-brightgreen.svg)]()

---

## 📌 1. Project Overview

**SafeWalk** is an AI-powered real-time women's safety navigation network and risk briefing system. While conventional navigation platforms optimize purely for travel duration, SafeWalk evaluates pedestrian routes across **6 critical safety dimensions**—combining live crowdsourced reports, OpenStreetMap infrastructural data (streetlights, POIs, police proximity), real-time news alerts, and WHO/NCRB grounded RAG AI briefings.

### 🌟 Core Value Proposition
- **Global Usability:** Works in any city worldwide (Delhi, Tokyo, London, Lagos, New York) using Nominatim geocoding, OSRM foot routing, and Overpass API.
- **Real-Time Recency Decay Flywheel:** Incidents carry maximum weight ($1.0$) when fresh and automatically decay over time ($48$-hour half-life exponential curve), ensuring the map remains sensitive to immediate risks.
- **Natural Language Incident Reporting:** Women report harassment or unsafe areas in plain English or Hindi without complex forms—Gemini NLP extracts structured details automatically.
- **RAG-Grounded Safety Briefings:** Generates tailored 5-bullet route advisories grounded in official **WHO Safety Directives** and **NCRB Analytical Insights**.
- **Community Validation:** $3+$ community upvotes award a **Verified Badge** and apply a $1.3\times$ weight multiplier to high-risk zones.

---

## 🔄 2. How It Works (System Workflow & Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SAFEWALK WORKFLOW                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
   [User Input]          [Location & Route Engine]              [Safety Scoring Engine]
 Start & Destination  ──► Nominatim Geocoder (City/Coords)  ──► OSRM Foot Walking Routes
                         └─► Overpass API Safety Data          ├─► Streetlight Coverage
                             (Police, Lights, POIs)            ├─► Weighted Incident Decay
                                                               └─► Dark Alley Penalties
                                                                          │
                                                                          ▼
   [AI & RAG Layer]            [Community & News Flywheel]       [Dual Route Output]
 RAG WHO/NCRB Engine  ◄─── Real-Time Incident Persistence  ◄─── 🟢 Safest Route (Score: 84)
 Gemini 1.5 Briefing       ├─► Gemini NLP Text Parser          🔴 Fastest Route (Score: 52)
 5-Bullet Guidance         ├─► AI News & Alert Ingestor        📍 Danger Zone Markers
                           └─► 3+ Vote Community Verification
```

### Step-by-Step Execution Flow:
1. **Address Geocoding & City Detection:**
   The user enters a starting point and destination. `geocoder.geocode_address()` converts addresses to `(lat, lng)` coordinates and reverse-geocodes the location to identify the active city and country.
2. **OSRM Route Generation:**
   `router.get_alternative_routes()` queries OSRM (`router.project-osrm.org/route/v1/foot`) to fetch candidate walking paths.
3. **Multi-Factor Safety Scoring ($0 - 100$):**
   `safety_scorer.calculate_safety_score()` evaluates coordinates along each route:
   - **Time of Day:** Nighttime ($10	ext{ PM}-4	ext{ AM}$) applies up to $-30$ penalty.
   - **Weighted Incidents:** Sum of active incident weights $	imes$ severities near the route.
   - **Streetlights:** $+0$ for lit streets, $-20$ for unlit streets.
   - **POI Density:** High shop/amenity density adds up to $+15$ bonus.
   - **Police Proximity:** Police stations within $800	ext{m}$ add $+10$ bonus.
   - **Dark Alleys:** Narrow unlit paths apply $-15$ penalty.
   - Sorts routes so `routes[0]` is the **Safest Route** (Green) and `routes[-1]` is the **Fastest Route** (Red/Dashed).
4. **Natural Language Reporting & Decay Flywheel:**
   When a user reports an incident in plain text, `genai_layer.process_incident_report()` uses Gemini NLP to extract structured JSON. The incident is saved into SQLite (`safewalk.db`) and `report_manager.update_all_weights()` recalculates all incident weights using the 48-hour half-life decay formula:
   $$	ext{Weight} = e^{-0.693 	imes rac{	ext{hours\_ago}}{48}} 	imes 	ext{Trust Modifier} 	imes 	ext{Verified Bonus}$$
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
│   ├── genai_layer.py                # Gemini 1.5 Flash: Briefings, Incident NLP, SOS SMS
│   ├── news_incident_fetcher.py       # AI News Ingestion: News alerts & NCRB data fetcher
│   └── rag_knowledge.py               # RAG Engine: WHO Guidelines + NCRB Insights vector store
│
├── backend/                          # Core Navigation & Database Engine
│   ├── safewalk_service.py            # Master Unified Integration API
│   ├── geocoder.py                    # Nominatim Geocoding & Reverse Geocoding with caching
│   ├── osm_safety_data.py             # Overpass API (Streetlights, POIs, Police, Alleys)
│   ├── router.py                      # OSRM Foot Router & Danger Zone Detector
│   ├── safety_scorer.py               # Multi-factor Safety Scoring Engine (0-100)
│   ├── report_manager.py              # Dynamic Weight Decay & Community Voting Engine
│   ├── setup_db.py                    # SQLite Database Schema & Delhi Demo Seed Data
│   ├── cli_demo.py                    # Interactive Terminal CLI Application
│   ├── test_integration.py            # End-to-End System Integration Test Suite
│   ├── test_m2_backend.py             # Backend Core Unit Test Suite
│   └── safewalk.db                    # SQLite Production Database
│
├── frontend/                         # User Interface Layer
│   └── app.py                         # Interactive Streamlit Web UI (Folium map, live feed, SOS)
│
├── .env                              # Environment Variables (GEMINI_API_KEY)
├── requirements.txt                  # Python Dependencies
└── README.md                         # Project Documentation
```

---

## ⚡ 4. Setup & Running Guide

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

### 2️⃣ Running the Interactive Terminal Application (CLI)

To test all SafeWalk features interactively in your terminal:

```bash
python backend/cli_demo.py
```

#### Interactive Terminal Features:
```text
============================================================
   🛡️  SAFEWALK INTERACTIVE USER TERMINAL DEMO
============================================================
Current Selected City: Delhi
1. 🗺️  Plan Safe Walking Route (Start -> Destination)
2. 📢  Report Safety Incident in Plain Text (Gemini NLP)
3. 📰  Fetch & Ingest Live News Incidents for City (AI News)
4. 🔥  View Recent Reports & Upvote Incidents
5. 🧠  Ask SafeWalk AI Assistant (RAG WHO/NCRB Knowledge)
6. 🌐  Change Selected City
7. ❌  Exit Demo
============================================================
```

---

### 3️⃣ Running Test Suites

#### Run Backend Unit Tests:
```bash
python backend/test_m2_backend.py
```

#### Run End-to-End Integration Tests:
```bash
python backend/test_integration.py
```

---

### 4️⃣ Running the Streamlit Web Application

To launch the web interface:

```bash
streamlit run frontend/app.py
```

---

## 🏆 5. Key Differentiators & Judge Talking Points

| Feature | Competitors (Google Maps, Waze) | SafeWalk v2.0 |
| :--- | :--- | :--- |
| **Route Optimization** | Purely fastest time ($m/min$) | Dual Routes: **Safest** ($0-100$) vs **Fastest** |
| **Incident Decay** | Static or binary flags | Exponential decay curve ($48	ext{h}$ half-life) |
| **Reporting Interface** | Multi-step manual forms | Natural Language text (English/Hindi) via Gemini NLP |
| **AI Safety Guidance** | None | 5-bullet briefing grounded in WHO/NCRB RAG context |
| **Community Trust** | Unverified user reports | 3+ upvote verification badge & $1.3	imes$ weight boost |
| **Global Scale** | Limited to partnered cities | Global support for any city via OpenStreetMap & Nominatim |

---

## 📜 6. License & Credits

Built with ❤️ by **Team SafeWalk** (UPES Dehradun, 2026).  
Powered by **Google Gemini AI**, **OpenStreetMap**, **OSRM**, **ReportLab**, and **Streamlit**.
