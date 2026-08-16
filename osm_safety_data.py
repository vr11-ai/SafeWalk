# osm_safety_data.py — MEMBER 2 OWNS THIS FILE
import requests
from typing import Optional, Dict, Any

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
CACHE_OSM: Dict[tuple, Dict[str, Any]] = {}
_OVERPASS_DISABLED = False

def _fetch_osm_safety_bundle(lat: float, lng: float) -> Dict[str, Any]:
    """
    Fetches a consolidated bundle of OSM safety data (streetlights, POIs, police, alleys)
    around a coordinate with coordinate caching and graceful offline fallback.
    """
    global _OVERPASS_DISABLED
    key = (round(lat, 2), round(lng, 2))
    if key in CACHE_OSM:
        return CACHE_OSM[key]

    bundle = {
        "streetlights": None,
        "poi_count": 6,
        "police": False,
        "dark_alleys": False
    }

    if _OVERPASS_DISABLED:
        CACHE_OSM[key] = bundle
        return bundle

    query = f"""
    [out:json][timeout:2];
    (
      node["highway"="street_lamp"](around:200, {lat}, {lng});
      way["lit"="yes"](around:200, {lat}, {lng});
      way["lit"="no"](around:200, {lat}, {lng});
      node["amenity"="police"](around:800, {lat}, {lng});
      way["amenity"="police"](around:800, {lat}, {lng});
      node["amenity"](around:250, {lat}, {lng});
      node["shop"](around:250, {lat}, {lng});
      way["highway"="alley"](around:150, {lat}, {lng});
    );
    out body;
    """

    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": "SafeWalk-App/2.0 (hackathon-safewalk@upes.ac.in)"},
            timeout=2.0
        )
        if resp.status_code == 200:
            elements = resp.json().get("elements", [])
            poi_count = 0
            has_lit = False
            has_unlit = False
            has_police = False
            has_alley = False

            for el in elements:
                tags = el.get("tags", {})
                if tags.get("highway") == "street_lamp" or tags.get("lit") == "yes":
                    has_lit = True
                if tags.get("lit") == "no":
                    has_unlit = True
                if tags.get("amenity") == "police":
                    has_police = True
                if tags.get("highway") == "alley" or (tags.get("highway") in ["footway", "path"] and tags.get("lit") == "no"):
                    has_alley = True
                if "amenity" in tags or "shop" in tags:
                    poi_count += 1

            if has_lit:
                bundle["streetlights"] = True
            elif has_unlit:
                bundle["streetlights"] = False
            else:
                bundle["streetlights"] = None

            bundle["poi_count"] = max(1, poi_count)
            bundle["police"] = has_police
            bundle["dark_alleys"] = has_alley

            CACHE_OSM[key] = bundle
            return bundle
        elif resp.status_code in [429, 504, 503]:
            # Rate limited or server busy: disable live requests temporarily for session
            _OVERPASS_DISABLED = True
    except Exception:
        _OVERPASS_DISABLED = True

    # Safe default heuristics when network/Overpass API is slow
    CACHE_OSM[key] = bundle
    return bundle

def has_streetlights(lat: float, lng: float) -> Optional[bool]:
    """
    Returns True if streetlights or lit streets are present,
    False if explicitly unlit, and None if undetermined.
    """
    data = _fetch_osm_safety_bundle(lat, lng)
    return data.get("streetlights")

def get_poi_count(lat: float, lng: float) -> int:
    """
    Returns the count of active Points of Interest (shops, amenities) near the coordinates.
    """
    data = _fetch_osm_safety_bundle(lat, lng)
    return data.get("poi_count", 6)

def has_police_nearby(lat: float, lng: float) -> bool:
    """
    Returns True if a police station/checkpoint is within 800m.
    """
    data = _fetch_osm_safety_bundle(lat, lng)
    return bool(data.get("police", False))

def has_dark_alleys(lat: float, lng: float) -> bool:
    """
    Returns True if narrow, unlit alleys or footpaths are present nearby.
    """
    data = _fetch_osm_safety_bundle(lat, lng)
    return bool(data.get("dark_alleys", False))
