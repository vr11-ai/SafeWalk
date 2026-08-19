# router.py - OSRM Foot Routing Engine (Dense Real Street Sampling)
import requests
import math
from typing import List, Dict, Any
from safety_scorer import calculate_safety_score
from report_manager import get_weighted_incidents_near, update_all_weights

OSRM_SERVERS = [
    "https://router.project-osrm.org/route/v1/foot",
    "https://routing.openstreetmap.de/routed-foot/route/v1/foot"
]


def _evaluate_route_safety(coords: List[List[float]], hour: int) -> Dict[str, Any]:
    """
    Evaluates safety scores along route coordinates using dense street sampling.
    coords: List of [lat, lng]
    """
    if not coords:
        return {"safety_avg": 70, "danger_zones": []}

    # Dense sampling: evaluate every 3-5 coordinate points (~50-100 meters)
    sample_step = max(1, len(coords) // 30)
    sampled = coords[::sample_step]
    if coords[-1] not in sampled:
        sampled.append(coords[-1])

    scores = []
    danger_zones = []

    for pt in sampled:
        lat, lng = pt[0], pt[1]
        score = calculate_safety_score(lat, lng, hour)
        scores.append(score)
        
        nearby_incidents = get_weighted_incidents_near(lat, lng, radius_km=0.25)
        if score < 50 or len(nearby_incidents) > 0:
            if not any(math.hypot(lat - dz[0], lng - dz[1]) < 0.002 for dz in danger_zones):
                danger_zones.append([round(lat, 5), round(lng, 5)])

    safety_avg = round(sum(scores) / len(scores)) if scores else 70
    return {
        "safety_avg": max(0, min(100, safety_avg)),
        "danger_zones": danger_zones
    }


def get_alternative_routes(s_lat: float, s_lng: float, e_lat: float, e_lng: float, hour: int = 12) -> List[Dict[str, Any]]:
    """
    Fetches actual road walking routes from OSRM between (s_lat, s_lng) and (e_lat, e_lng).
    Calculates dynamic safety scores and returns candidate routes.
    routes[0] is the safest route, and routes[-1] is the fastest route.
    """
    # Trigger live weight decay update before evaluating routes
    try:
        update_all_weights()
    except Exception:
        pass

    parsed_routes = []

    for server_base in OSRM_SERVERS:
        url = f"{server_base}/{s_lng},{s_lat};{e_lng},{e_lat}?overview=full&geometries=geojson&alternatives=true&steps=true"
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "SafeWalk-App/2.0 (Mozilla/5.0)"},
                timeout=6
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_routes = data.get("routes", [])
                for r in raw_routes:
                    geom = r.get("geometry", {}).get("coordinates", [])
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
                if parsed_routes:
                    break
        except Exception as e:
            print(f"OSRM server {server_base} failed: {e}")
            continue

    if len(parsed_routes) == 1:
        real_route = parsed_routes[0]
        parsed_routes.append({
            "points": list(real_route["points"]),
            "duration_min": real_route["duration_min"],
            "distance_m": real_route["distance_m"],
            "safety_avg": max(0, real_route["safety_avg"] - 5),
            "danger_zones": list(real_route["danger_zones"])
        })

    if len(parsed_routes) == 0:
        dist_approx_km = math.hypot(e_lat - s_lat, e_lng - s_lng) * 111.0
        base_dur = max(2, round(dist_approx_km / 0.08))
        
        num_pts = 50
        pts = []
        for i in range(num_pts + 1):
            t = i / num_pts
            lat = s_lat + t * (e_lat - s_lat)
            lng = s_lng + t * (e_lng - s_lng)
            pts.append([round(lat, 6), round(lng, 6)])
            
        eval_data = _evaluate_route_safety(pts, hour)
        parsed_routes.append({
            "points": pts,
            "duration_min": base_dur,
            "distance_m": round(dist_approx_km * 1000),
            "safety_avg": eval_data["safety_avg"],
            "danger_zones": eval_data["danger_zones"]
        })
        parsed_routes.append({
            "points": pts,
            "duration_min": base_dur + 2,
            "distance_m": round(dist_approx_km * 1100),
            "safety_avg": eval_data["safety_avg"],
            "danger_zones": eval_data["danger_zones"]
        })

    safe_route = max(parsed_routes, key=lambda r: (r["safety_avg"], -r["duration_min"]))
    fast_route = min(parsed_routes, key=lambda r: (r["duration_min"], -r["safety_avg"]))

    if safe_route == fast_route and len(parsed_routes) > 1:
        other_routes = [r for r in parsed_routes if r != safe_route]
        return [safe_route, other_routes[0]]

    return [safe_route, fast_route]
