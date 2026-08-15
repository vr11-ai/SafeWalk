# genai_layer.py — VIDIT OWNS THIS FILE
# 4 Gemini Features: Route Safety Briefing, Incident NLP Parser, SOS SMS Generator, City Overview

import os
import json
import re
import google.generativeai as genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Helper to load API key from .env file or os.environ
def get_api_key():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                        return v.strip("'\" ")
    return "YOUR_GEMINI_KEY"

API_KEY = get_api_key()
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')


# FEATURE 1 — Route Safety Briefing
def generate_safety_briefing(route_data, time_str, city, country, verified_reports=0, recent_reports=0):
    """
    Generates a 5-bullet route safety briefing aware of real-time crowdsourced reports.
    """
    if recent_reports > 0:
        realtime_ctx = f"{recent_reports} reports in last 24h. {verified_reports} verified by community."
    else:
        realtime_ctx = "No recent reports in this area."

    avg_score = route_data.get("average", "N/A") if isinstance(route_data, dict) else route_data

    prompt = f'''
You are SafeWalk safety advisor for women in {city}, {country}.
Safety score: {avg_score}/100
Time: {time_str}
Real-time data: {realtime_ctx}

Give exactly 5 bullet points:
1. One-line route assessment at this time
2. City-specific safety context for {city}
3. What to do if unsafe (include local emergency number)
4. Take this route or use transport?
5. One empowering tip specific to {city}

Tone: Direct, respectful. NOT fearmongering. Under 150 words.
'''
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Safety briefing unavailable ({e}). Please exercise standard safety precautions in {city}."


# FEATURE 2 — Incident Report NLP (extracts structured JSON from free text)
def process_incident_report(user_text, city, country):
    """
    Extracts structured incident data from unstructured user text using Gemini.
    Returns a dict with location_description, incident_type, time_of_day, severity, confidence.
    """
    prompt = f'''
Extract incident details from this report.
Reporter is in: {city}, {country}
Report: "{user_text}"

Return ONLY valid JSON:
{{
  "location_description": "specific place mentioned",
  "incident_type": "harassment/following/theft/unsafe_area/other",
  "time_of_day": "morning/afternoon/evening/night/unknown",
  "severity": 1,
  "confidence": 0.0
}}

severity: 1=uncomfortable 2=threatened 3=attacked
confidence: 0.0-1.0 how clearly location is described
'''
    try:
        resp = model.generate_content(prompt).text
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        if match:
            return json.loads(match.group())
        return None
    except Exception as e:
        print(f"Error processing incident report: {e}")
        return None


# FEATURE 3 — SOS Message Generator
def generate_sos_message(name, location, destination, city):
    """
    Generates an urgent SMS SOS alert under 160 characters.
    """
    prompt = f'''
Write urgent SOS SMS under 160 characters.
Person: {name} in {city}. Last location: {location}.
Going to: {destination}. Ask recipient to call immediately.
'''
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"EMERGENCY: {name} needs help near {location}, {city} en route to {destination}. Call immediately!"


# FEATURE 4 — City Overview for new cities with no crowdsourced data yet
def get_city_safety_overview(city, country):
    """
    Generates a general women's safety overview for any city worldwide.
    """
    prompt = f'''
Women's safety overview for {city}, {country}.
Include: safer vs concerning area types, time-of-day patterns,
local emergency number for women, one cultural safety tip.
Under 150 words. Label as AI-generated, not real-time.
'''
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Safety overview for {city}, {country} currently unavailable."
