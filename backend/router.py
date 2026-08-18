# router.py — MEMBER 2 OWNS THIS FILE
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from safety_scorer import calculate_safety_score


def get_alternative_routes(s_lat, s_lng, e_lat, e_lng, hour):
    # Calculate midpoints for route variations
    mid_lat = (s_lat + e_lat) / 2
    mid_lng = (s_lng + e_lng) / 2

    score_safe = calculate_safety_score(s_lat, s_lng, hour)
    score_fast = max(20, score_safe - 26)

    safe_route = {
        'points': [[s_lat, s_lng], [mid_lat + 0.004, mid_lng + 0.004], [e_lat, e_lng]],
        'safety_avg': int(score_safe),
        'duration_min': 22,
        'danger_zones': []
    }

    fast_route = {
        'points': [[s_lat, s_lng], [mid_lat - 0.003, mid_lng - 0.003], [e_lat, e_lng]],
        'safety_avg': int(score_fast),
        'duration_min': 17,
        'danger_zones': [[mid_lat - 0.003, mid_lng - 0.003]]
    }

    return [safe_route, fast_route]
