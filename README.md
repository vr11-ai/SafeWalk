# SafeWalk v2.0
> **"Google Maps shows the fastest route. SafeWalk shows the safest route for any city worldwide, updated in real-time by women themselves."**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Gemini AI](https://img.shields.io/badge/AI-Gemini%20AI-orange.svg)](https://deepmind.google/technologies/gemini/)
[![RAG Architecture](https://img.shields.io/badge/RAG-WHO%20%26%20NCRB%20Grounded-green.svg)]()
[![OpenStreetMap / OSRM](https://img.shields.io/badge/Navigation-OSRM%20%2B%20Leaflet-brightgreen.svg)]()
[![Flask API](https://img.shields.io/badge/API-Flask%20REST-blue.svg)]()
[![HTML5 / CSS3 / JS](https://img.shields.io/badge/Frontend-HTML%20%2B%20CSS%20%2B%20JS-violet.svg)]()

---

## Overview

SafeWalk v2.0 is an AI-powered women's safety navigation platform featuring:
- **HTML/CSS/JS Interactive Frontend**: Plus Jakarta Sans typography, light glassmorphic theme, micro-animations, Leaflet map, city landmark suggestions, live community incident feed, and RAG AI assistant.
- **Flask REST API Server (`api_server.py`)**: Bridges the web frontend to the Python backend safety services.
- **Multi-City Precision Geocoding Engine**: Supports 14+ global & Indian cities with landmark alias resolution.
- **Real-Road OSRM Routing & Safety Scorer**: Evaluates street safety dynamically with exponential time-decay weights.
- **Gemini NLP & RAG Knowledge Engine**: Incident report parsing, real-world news ingestion, emergency SOS generator, and safety advice grounded in WHO/NCRB guidelines.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install flask flask-cors
```

### 2. Launch SafeWalk Web Application
```bash
python api_server.py
```
Open **http://localhost:5000** in your browser.

---

## Team Credits & Roles

SafeWalk v2.0 was designed and developed by **Team SafeWalk** (UPES Dehradun, 2026):

- **Vidit Raturi** — **Team Lead**  
  *Full-Stack System Integration, HTML/CSS/JS Web App, Flask REST API, End-to-End Feature Development, Security Hardening, Dynamic Decay Weight Engine, High-Precision Multi-Stage Geocoding.*
- **Vanshika** — **Frontend Lead**  
  *Dashboard UI/UX, Map Component Architecture, Live Incident Feed Components, and SOS Interface.*
- **Ritika** — **Backend Foundation Lead**  
  *SQLite Database Schema Architecture, Initial OSRM & Overpass API Routing Foundation, and Core Safety Scoring Base.*

---

## License & Credits

Built with care by **Team SafeWalk** (UPES Dehradun, 2026).  
Powered by **Google Gemini AI**, **OpenStreetMap**, **OSRM**, **Leaflet.js**, and **Flask**.
