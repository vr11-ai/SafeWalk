# test_m2_backend.py — Test suite for Member 2 Backend Deliverables
import os
import sys
import sqlite3
import math
from datetime import datetime, timedelta

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from setup_db import init_database, save_incident
from report_manager import (
    calculate_weight,
    update_all_weights,
    get_weighted_incidents_near,
    upvote_incident,
    downvote_incident,
    get_recent_reports_in_city,
    get_city_stats
)
from geocoder import geocode_address, get_city_country_from_coords
from osm_safety_data import (
    has_streetlights,
    get_poi_count,
    has_police_nearby,
    has_dark_alleys
)
from safety_scorer import calculate_safety_score
from router import get_alternative_routes

def test_database_init():
    print("\n--- Testing Database Init & Seeding ---")
    if os.path.exists('safewalk.db'):
        try:
            os.remove('safewalk.db')
        except Exception:
            pass
    init_database()
    conn = sqlite3.connect('safewalk.db')
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert 'incidents' in tables, "incidents table missing"
    assert 'session_votes' in tables, "session_votes table missing"

    cursor = conn.execute("SELECT COUNT(*) FROM incidents WHERE city='Delhi'")
    count = cursor.fetchone()[0]
    print(f"Delhi incidents seeded: {count}")
    assert count >= 15, f"Expected at least 15 Delhi incidents, got {count}"
    conn.close()
    print("Database init & 15+ Delhi incidents verification PASSED.")

def test_weight_engine():
    print("\n--- Testing Weight Engine & Recency Decay ---")
    w_1h = calculate_weight(1.0)
    w_24h = calculate_weight(24.0)
    w_48h = calculate_weight(48.0)
    w_168h = calculate_weight(168.0) # 7 days
    w_720h = calculate_weight(720.0) # 30 days

    print(f"Weight at 1h: {w_1h} (Target ~1.0, actual: {w_1h})")
    print(f"Weight at 24h: {w_24h} (Target ~0.7-0.8)")
    print(f"Weight at 48h: {w_48h} (Target ~0.5, actual: {w_48h})")
    print(f"Weight at 168h: {w_168h} (Target ~0.1-0.2)")
    print(f"Weight at 720h: {w_720h} (Target ~0.01-0.03, actual: {w_720h})")

    assert 0.95 <= w_1h <= 1.0, f"w_1h should be close to 1.0, got {w_1h}"
    assert 0.45 <= w_48h <= 0.55, f"w_48h should be close to 0.5, got {w_48h}"
    assert 0.01 <= w_720h <= 0.05, f"w_720h should be close to 0.02, got {w_720h}"

    # Test trust and verification multipliers
    w_up = calculate_weight(1.0, upvotes=2, downvotes=0)
    w_ver = calculate_weight(1.0, upvotes=3, downvotes=0)
    assert w_up > w_1h, "Upvoted incident should have higher weight"
    assert w_ver >= w_up * 1.25, "3+ upvotes should give verified bonus multiplier"
    print("Weight engine calculations PASSED.")

def test_voting_and_deduplication():
    print("\n--- Testing Voting & Session Deduplication ---")
    # Save a fresh test incident
    save_incident(28.6315, 77.2167, "test_incident", 2, "night", "Delhi", "India", "Test description")
    conn = sqlite3.connect('safewalk.db')
    inc_id = conn.execute("SELECT id FROM incidents WHERE type='test_incident' ORDER BY id DESC LIMIT 1").fetchone()[0]
    conn.close()

    session_a = "user_session_alpha"
    session_b = "user_session_beta"
    session_c = "user_session_gamma"

    # First vote from session_a
    res1 = upvote_incident(inc_id, session_a)
    assert res1 is True, "First upvote should succeed"

    # Duplicate vote from session_a should fail
    res2 = upvote_incident(inc_id, session_a)
    assert res2 is False, "Duplicate upvote from same session must fail"

    # 2nd vote from session_b
    upvote_incident(inc_id, session_b)
    # 3rd vote from session_c -> should auto-verify
    upvote_incident(inc_id, session_c)

    conn = sqlite3.connect('safewalk.db')
    row = conn.execute("SELECT upvotes, verified FROM incidents WHERE id=?", (inc_id,)).fetchone()
    conn.close()
    assert row[0] == 3, f"Expected 3 upvotes, got {row[0]}"
    assert row[1] == 1, "Incident must be auto-verified after 3 upvotes"
    print("Voting and deduplication PASSED.")

def test_city_stats_and_feed():
    print("\n--- Testing City Stats & Live Feed ---")
    update_all_weights()
    stats = get_city_stats("Delhi")
    print("Delhi Stats:", stats)
    assert stats['total'] >= 15, "Total incidents should be >= 15"
    assert 'verified' in stats
    assert 'last_24h' in stats
    assert 'avg_severity' in stats

    feed = get_recent_reports_in_city("Delhi", limit=5)
    assert len(feed) > 0, "Feed should return recent incidents"
    print(f"Feed returned {len(feed)} reports for Delhi.")
    print("City stats and feed PASSED.")

def test_geocoder():
    print("\n--- Testing Geocoder & Reverse Geocoder ---")
    # Test Delhi
    lat, lng = geocode_address("Connaught Place, Delhi")
    print(f"Connaught Place coords: ({lat}, {lng})")
    assert lat is not None and lng is not None
    assert 28.0 <= lat <= 29.0 and 76.0 <= lng <= 78.0

    city, country = get_city_country_from_coords(lat, lng)
    print(f"Reverse geocode for CP: {city}, {country}")
    assert "delhi" in city.lower() or "india" in country.lower()

    # Test Tokyo (Global support)
    t_lat, t_lng = geocode_address("Shinjuku Station, Tokyo")
    print(f"Shinjuku coords: ({t_lat}, {t_lng})")
    assert t_lat is not None and t_lng is not None
    assert 35.0 <= t_lat <= 36.0 and 139.0 <= t_lng <= 140.0

    t_city, t_country = get_city_country_from_coords(t_lat, t_lng)
    print(f"Reverse geocode for Shinjuku: {t_city}, {t_country}")
    print("Geocoder PASSED.")

def test_osm_safety_data():
    print("\n--- Testing OSM Safety Data ---")
    lit = has_streetlights(28.6315, 77.2167)
    pois = get_poi_count(28.6315, 77.2167)
    police = has_police_nearby(28.6315, 77.2167)
    alleys = has_dark_alleys(28.6315, 77.2167)
    print(f"OSM Data for CP - Streetlights: {lit}, POIs: {pois}, Police: {police}, Alleys: {alleys}")
    assert isinstance(pois, int)
    assert isinstance(police, bool)
    assert isinstance(alleys, bool)
    print("OSM Safety Data PASSED.")

def test_safety_scorer():
    print("\n--- Testing Safety Scorer ---")
    # Daytime score vs Nighttime score
    score_day = calculate_safety_score(28.6315, 77.2167, hour=14)
    score_night = calculate_safety_score(28.6315, 77.2167, hour=23)
    print(f"CP Safety Score - Day (14:00): {score_day}/100, Night (23:00): {score_night}/100")
    assert score_day > score_night, "Day score should be higher than night score"

    # Simulate fresh severe incident at clean location and verify score drops
    test_lat, test_lng = 28.4500, 77.0500
    pre_score = calculate_safety_score(test_lat, test_lng, hour=12)
    save_incident(test_lat, test_lng, "harassment", 3, "day", "Delhi", "India", "Fresh urgent incident")
    update_all_weights()
    post_score = calculate_safety_score(test_lat, test_lng, hour=12)
    print(f"Clean Location - Pre-incident score: {pre_score}, Post-incident score: {post_score}")
    assert post_score < pre_score, f"Score must drop after fresh incident reported (pre: {pre_score}, post: {post_score})"
    print("Safety Scorer PASSED.")

def test_router():
    print("\n--- Testing Router & OSRM Alternative Routes ---")
    # Connaught Place to Lajpat Nagar
    s_lat, s_lng = 28.6315, 77.2167
    e_lat, e_lng = 28.5677, 77.2433
    routes = get_alternative_routes(s_lat, s_lng, e_lat, e_lng, hour=22)

    assert len(routes) >= 2, f"Expected at least 2 routes, got {len(routes)}"
    safe_route = routes[0]
    fast_route = routes[-1]

    print(f"Safe Route - Duration: {safe_route['duration_min']} min, Safety: {safe_route['safety_avg']}/100, Danger Zones: {len(safe_route['danger_zones'])}")
    print(f"Fast Route - Duration: {fast_route['duration_min']} min, Safety: {fast_route['safety_avg']}/100, Danger Zones: {len(fast_route['danger_zones'])}")

    assert "points" in safe_route and len(safe_route["points"]) > 0
    assert "safety_avg" in safe_route
    assert "duration_min" in safe_route
    assert "danger_zones" in safe_route
    assert safe_route["safety_avg"] >= fast_route["safety_avg"], "Safe route must have safety score >= fast route"
    print("Router & OSRM Alternatives PASSED.")

if __name__ == "__main__":
    print("==================================================")
    print("  RUNNING COMPLETE MEMBER 2 BACKEND TEST SUITE   ")
    print("==================================================")
    test_database_init()
    test_weight_engine()
    test_voting_and_deduplication()
    test_city_stats_and_feed()
    test_geocoder()
    test_osm_safety_data()
    test_safety_scorer()
    test_router()
    print("\n==================================================")
    print("  ALL MEMBER 2 BACKEND TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")
