# safety_scorer.py - Dynamic Continuous Time & Live Weight Safety Scorer
import math
from osm_safety_data import (has_streetlights, get_poi_count,
                             has_police_nearby, has_dark_alleys)
from report_manager import get_weighted_incidents_near, update_all_weights


def _calculate_dynamic_time_penalty(hour: int) -> int:
    """
    Calculates a smooth mathematical time-of-day penalty using a continuous sinusoidal curve.
    Peak darkness (2:00 AM) = -30 points penalty.
    Peak daylight (12:00 PM) = 0 points penalty.
    """
    # Convert hour (0-23) to radian angle centered on 14:00 (peak daylight)
    angle = (hour - 14) * (2 * math.pi / 24)
    # Cosine curve ranges from 1.0 (at 14:00) to -1.0 (at 02:00 AM)
    daylight_factor = (math.cos(angle) + 1.0) / 2.0  # 0.0 (night) to 1.0 (day)
    penalty = round((1.0 - daylight_factor) * 30)
    return max(0, min(30, penalty))


def calculate_safety_score(lat: float, lng: float, hour: int = 12) -> int:
    score = 100

    # Factor 1: Smooth Continuous Time of Day Penalty
    time_penalty = _calculate_dynamic_time_penalty(hour)
    score -= time_penalty

    # Factor 2: Live Dynamic Weighted Incidents (Recency Decay + Trust + Verification)
    incidents = get_weighted_incidents_near(lat, lng, radius_km=0.3)
    if incidents:
        weight_sum = sum(i['weight'] * i['severity'] for i in incidents)
        score -= min(weight_sum * 12, 50)  # Max incident penalty -50
        if any(i.get('verified') for i in incidents):
            score -= 10  # Verified active danger zone extra penalty

    # Factor 3: Streetlight Coverage (OSM 110m Fine-Grained Grid)
    lit = has_streetlights(lat, lng)
    if lit is False:
        score -= 20
    elif lit is None:
        score -= 5

    # Factor 4: POI Density (Active Commercial Stores / Open Establishments)
    pois = get_poi_count(lat, lng)
    if pois > 10:
        score += 15
    elif pois > 5:
        score += 8
    elif pois == 0:
        score -= 10

    # Factor 5: Police Station Proximity (<800m)
    if has_police_nearby(lat, lng):
        score += 10

    # Factor 6: Dark Alleys / Unlit Footpaths
    if has_dark_alleys(lat, lng):
        score -= 15

    return max(0, min(100, int(score)))
