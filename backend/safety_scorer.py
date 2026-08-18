# safety_scorer.py — MEMBER 2 OWNS THIS FILE (UPDATED v2.0)
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from osm_safety_data import (has_streetlights, get_poi_count,
                             has_police_nearby, has_dark_alleys)
from report_manager import get_weighted_incidents_near


def calculate_safety_score(lat, lng, hour):
    score = 100
    # Factor 1: Time of day (universal)
    if hour >= 22 or hour <= 4:
        score -= 30
    elif 20 <= hour < 22:
        score -= 20
    elif 5 <= hour < 7:
        score -= 10

    # Factor 2: WEIGHTED incidents — KEY CHANGE FROM v1.0
    incidents = get_weighted_incidents_near(lat, lng, 0.3)
    if incidents:
        weight_sum = sum(i['weight'] * i['severity'] for i in incidents)
        score -= min(weight_sum * 10, 45)
        if any(i.get('verified') for i in incidents):
            score -= 10  # verified = extra penalty

    # Factor 3: Streetlights (OSM global)
    lit = has_streetlights(lat, lng)
    if lit is False:
        score -= 20
    elif lit is None:
        score -= 5

    # Factor 4: POI density (OSM global)
    pois = get_poi_count(lat, lng)
    if pois > 10:
        score += 15
    elif pois > 5:
        score += 8
    elif pois == 0:
        score -= 10

    # Factor 5: Police nearby (OSM global)
    if has_police_nearby(lat, lng):
        score += 10

    # Factor 6: Dark alleys
    if has_dark_alleys(lat, lng):
        score -= 15

    return max(0, min(100, score))
