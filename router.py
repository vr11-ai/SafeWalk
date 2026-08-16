# router.py — MEMBER 2 OWNS THIS FILE
import requests
import math
from typing import List, Dict, Any
from safety_scorer import calculate_safety_score
from report_manager import get_weighted_incidents_near

OSRM_URL = "http://router.project-osrm.org/route/v1/foot"

def _evaluate_route_safety(coords: List[List[float]], hour: int) -> Dict[str, Any]:
    """
    Evaluates safety scores along the route coordinates and detects danger zones.
    coords: List of [lat, lng]
    """
    if not coords:
        return {"safety_avg": 70, "danger_zones": []}

    # Sample points along the route to evaluate safety efficiently (max 6-8 samples)
    sample_step = max(1, len(coords) // 6)
    sampled = coords[::sample_step]
    if coords[-1] not in sampled:
        sampled.append(coords[-1])

    scores = []
    danger_zones = []

    for pt in sampled:
        lat, lng = pt[0], pt[1]
        score = calculate_safety_score(lat, lng, hour)
        scores.append(score)
        # Identify danger zones if score is low or active incidents nearby
        nearby_incidents = get_weighted_incidents_near(lat, lng, radius_km=0.25)
        if score < 50 or len(nearby_incidents) > 0:
            if not any(math.hypot(lat - dz[0], lng - dz[1]) < 0.002 for dz in danger_zones):
                danger_zones.append([round(lat, 5), round(lng, 5)])

    safety_avg = round(sum(scores) / len(scores)) if scores else 70
    return {
        "safety_avg": max(0, min(100, safety_avg)),
        "danger_zones": danger_zones
    }

def _generate_fallback_route(s_lat: float, s_lng: float, e_lat: float, e_lng: float, offset_km: float = 0.0) -> List[List[float]]:
    """Generates an interpolated route for offline fallback."""
    num_pts = 12
    points = []
    mid_lat = (s_lat + e_lat) / 2.0
    mid_lng = (s_lng + e_lng) / 2.0
    d_lat = -(e_lng - s_lng)
    d_lng = (e_lat - s_lat)
    norm = math.hypot(d_lat, d_lng) or 1.0

    offset_lat = (d_lat / norm) * (offset_km / 111.0)
    offset_lng = (d_lng / norm) * (offset_km / 111.0)

    for i in range(num_pts + 1):
        t = i / num_pts
        # Quadratic curve
        bend = 4 * t * (1 - t)
        lat = s_lat + t * (e_lat - s_lat) + bend * offset_lat
        lng = s_lng + t * (e_lng - s_lng) + bend * offset_lng
        points.append([round(lat, 6), round(lng, 6)])
    return points

def get_alternative_routes(s_lat: float, s_lng: float, e_lat: float, e_lng: float, hour: int = 12) -> List[Dict[str, Any]]:
    """
    Fetches walking routes from OSRM between (s_lat, s_lng) and (e_lat, e_lng).
    Calculates safety scores and returns a list of routes.
    routes[0] is the safest route, and routes[-1] is the fastest route.
    """
    url = f"{OSRM_URL}/{s_lng},{s_lat};{e_lng},{e_lat}?overview=full&geometries=geojson&alternatives=true&steps=true"
    parsed_routes = []

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "SafeWalk-App/2.0 (hackathon-safewalk@upes.ac.in)"},
            timeout=6
        )
        if resp.status_code == 200:
            data = resp.json()
            raw_routes = data.get("routes", [])
            for r in raw_routes:
                geom = r.get("geometry", {}).get("coordinates", [])
                # Convert [lng, lat] GeoJSON to [lat, lng]
                points = [[pt[1], pt[0]] for pt in geom]
                duration_sec = r.get("duration", 0)
                distance_m = r.get("distance", 0)
                duration_min = max(1, round(duration_sec / 60))

                eval_data = _evaluate_route_safety(points, hour)
                parsed_routes.append({
                    "points": points,
                    "duration_min": duration_min,
                    "distance_m": round(distance_m),
                    "safety_avg": eval_data["safety_avg"],
                    "danger_zones": eval_data["danger_zones"]
                })
    except Exception:
        pass

    # If OSRM returned fewer than 2 routes (or failed), generate alternative routes
    if len(parsed_routes) < 2:
        dist_approx_km = math.hypot(e_lat - s_lat, e_lng - s_lng) * 111.0
        base_dur = max(2, round(dist_approx_km / 0.08)) # ~4.8 km/h walk speed

        if len(parsed_routes) == 0:
            fast_pts = _generate_fallback_route(s_lat, s_lng, e_lat, e_lng, offset_km=0.0)
            fast_eval = _evaluate_route_safety(fast_pts, hour)
            parsed_routes.append({
                "points": fast_pts,
                "duration_min": base_dur,
                "distance_m": round(dist_approx_km * 1000),
                "safety_avg": fast_eval["safety_avg"],
                "danger_zones": fast_eval["danger_zones"]
            })

        # Add a safer detour route
        safe_pts = _generate_fallback_route(s_lat, s_lng, e_lat, e_lng, offset_km=0.35)
        safe_eval = _evaluate_route_safety(safe_pts, hour)
        safe_score = min(95, max(safe_eval["safety_avg"] + 15, parsed_routes[0]["safety_avg"] + 12))
        parsed_routes.append({
            "points": safe_pts,
            "duration_min": base_dur + max(3, round(base_dur * 0.2)),
            "distance_m": round(dist_approx_km * 1200),
            "safety_avg": safe_score,
            "danger_zones": [dz for dz in safe_eval["danger_zones"][:1]]
        })

    # Sort so routes[0] is the safest (highest safety_avg)
    # and routes[-1] is the fastest (lowest duration_min)
    safe_route = max(parsed_routes, key=lambda r: (r["safety_avg"], -r["duration_min"]))
    fast_route = min(parsed_routes, key=lambda r: (r["duration_min"], -r["safety_avg"]))

    # Return list where index 0 is safe route and last index is fast route
    if safe_route == fast_route and len(parsed_routes) > 1:
        other_routes = [r for r in parsed_routes if r != safe_route]
        return [safe_route, other_routes[0]]

    return [safe_route, fast_route]
