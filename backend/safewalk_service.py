"""
SafeWalk Core Integration Service
Connects backend (geocoder, router, DB, safety scorer) with AI backend (Gemini NLP, RAG, News Fetcher, Briefings).
"""

import sys
import os
from typing import Dict, Any, Optional

# Add parent directory and backend/ai_backend to Python path for seamless imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
AI_BACKEND_DIR = os.path.join(BASE_DIR, "ai_backend")

for d in [BASE_DIR, BACKEND_DIR, AI_BACKEND_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Backend imports
from geocoder import geocode_address, get_city_country_from_coords
from router import get_alternative_routes
from safety_scorer import calculate_safety_score
from report_manager import (
    update_all_weights,
    get_weighted_incidents_near,
    get_city_stats,
    get_recent_reports_in_city,
    upvote_incident,
    downvote_incident,
    calculate_weight,
)
from setup_db import init_database, save_incident

# AI Backend imports
from genai_layer import (
    generate_safety_briefing,
    process_incident_report,
    generate_sos_message,
    get_city_safety_overview,
)
from rag_knowledge import query_rag_knowledge, get_safety_context
from news_incident_fetcher import fetch_news_incidents_for_city


def initialize_safewalk_system():
    """Initializes SQLite database and ensures seeds and weights are ready."""
    init_database()
    update_all_weights()
    print("SafeWalk Integrated System initialized successfully.")


def plan_safe_route(start_location: str, end_location: str, hour: int = 22) -> Dict[str, Any]:
    """
    End-to-End Route Planning Pipeline:
    1. Geocodes start and destination addresses.
    2. Identifies city and country.
    3. Calculates alternative walking routes (Safest vs Fastest) using OSRM + Safety Scorer.
    4. Fetches real-time community report statistics for the city.
    5. Generates RAG + Gemini powered 5-bullet safety briefing.
    """
    s_lat, s_lng = geocode_address(start_location)
    e_lat, e_lng = geocode_address(end_location)

    if s_lat is None or e_lat is None:
        return {
            "success": False,
            "error": "Could not geocode one or both addresses. Please try more specific locations.",
            "start_coords": (s_lat, s_lng),
            "end_coords": (e_lat, e_lng),
        }

    city, country = get_city_country_from_coords(s_lat, s_lng)

    update_all_weights()
    routes = get_alternative_routes(s_lat, s_lng, e_lat, e_lng, hour=hour)
    safest_route = routes[0]
    fastest_route = routes[-1]

    city_stats = get_city_stats(city)

    time_str = f"{hour:02d}:00"
    briefing = generate_safety_briefing(
        route_data=safest_route["safety_avg"],
        time_str=time_str,
        city=city,
        country=country,
        verified_reports=city_stats.get("verified", 0),
        recent_reports=city_stats.get("last_24h", 0),
    )

    recent_feed = get_recent_reports_in_city(city, limit=10)

    return {
        "success": True,
        "city": city,
        "country": country,
        "start": {"address": start_location, "lat": s_lat, "lng": s_lng},
        "destination": {"address": end_location, "lat": e_lat, "lng": e_lng},
        "routes": {
            "safest": safest_route,
            "fastest": fastest_route,
        },
        "city_stats": city_stats,
        "ai_safety_briefing": briefing,
        "recent_reports": recent_feed,
    }


def process_and_save_user_report(user_text: str, current_city: str = "Delhi", country: str = "India") -> Dict[str, Any]:
    """
    End-to-End Incident Reporting Pipeline:
    1. Gemini NLP parses free-text report into structured JSON.
    2. Geocodes extracted location description into lat/lng.
    3. Saves incident into database.
    4. Updates dynamic incident weights instantly so safety scores drop real-time.
    """
    nlp_res = process_incident_report(user_text, current_city, country)
    if not nlp_res:
        nlp_res = {
            "location_description": current_city,
            "incident_type": "unsafe_area",
            "time_of_day": "night",
            "severity": 2,
            "confidence": 0.5,
        }

    loc_desc = nlp_res.get("location_description", current_city)
    search_addr = f"{loc_desc}, {current_city}" if current_city not in loc_desc else loc_desc

    lat, lng = geocode_address(search_addr)
    if lat is None:
        lat, lng = geocode_address(current_city)

    inc_type = nlp_res.get("incident_type", "unsafe_area")
    severity = nlp_res.get("severity", 2)
    tod = nlp_res.get("time_of_day", "night")

    save_incident(
        lat=lat,
        lng=lng,
        inc_type=inc_type,
        severity=severity,
        time_of_day=tod,
        city=current_city,
        country=country,
        description=user_text,
    )

    update_all_weights()
    updated_stats = get_city_stats(current_city)

    return {
        "success": True,
        "nlp_parsed": nlp_res,
        "saved_location": {"address": search_addr, "lat": lat, "lng": lng},
        "city_stats": updated_stats,
    }


def ingest_city_news_reports(city: str = "Delhi", country: str = "India") -> Dict[str, Any]:
    """
    AI News Ingestion Pipeline:
    Fetches real-world reported safety incidents from news/NCRB bulletins for a city,
    geocodes them, saves them to the DB, and recalculates safety weights.
    """
    raw_news = fetch_news_incidents_for_city(city, country)
    ingested_count = 0

    for item in raw_news:
        loc_desc = item.get("location_description", city)
        search_addr = f"{loc_desc}, {city}" if city not in loc_desc else loc_desc

        lat, lng = geocode_address(search_addr)
        if lat is None:
            lat, lng = geocode_address(city)

        if lat is not None:
            save_incident(
                lat=lat,
                lng=lng,
                inc_type=item.get("incident_type", "unsafe_area"),
                severity=item.get("severity", 2),
                time_of_day=item.get("time_of_day", "night"),
                city=city,
                country=country,
                description=f"[{item.get('news_source', 'News Source')}] {item.get('description', '')}",
            )
            ingested_count += 1

    update_all_weights()
    updated_stats = get_city_stats(city)

    return {
        "success": True,
        "city": city,
        "ingested_count": ingested_count,
        "raw_news_fetched": raw_news,
        "updated_city_stats": updated_stats,
    }


def handle_vote(incident_id: int, session_id: str, vote_type: str = "up") -> Dict[str, Any]:
    """
    Community Validation Pipeline:
    1. Upvotes or Downvotes incident with session-based deduplication.
    2. Recalculates weight decay curve and verified status (3+ upvotes = verified).
    """
    if vote_type == "up":
        success = upvote_incident(incident_id, session_id)
    else:
        success = downvote_incident(incident_id, session_id)

    if success:
        update_all_weights()

    return {
        "success": success,
        "incident_id": incident_id,
        "vote_type": vote_type,
    }


def ask_safewalk_ai(user_query: str, city: str = "Delhi", country: str = "India") -> Dict[str, Any]:
    """
    RAG Assistant Query Pipeline:
    Retrieves WHO/NCRB guidelines and generates tailored AI advice.
    """
    return query_rag_knowledge(user_query, city=city, country=country)
