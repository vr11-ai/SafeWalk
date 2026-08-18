"""
High-Precision Geocoder Module using Multi-Stage Matching & OpenStreetMap Nominatim.
Converts local address strings, chowks, markets, and colleges to exact lat/lng coordinates.
"""

import time
import requests
import re
from functools import lru_cache
from typing import Tuple, Optional, List

_GEOCODE_CACHE = {}

# Exact High-Precision Landmark Coordinates Database
EXACT_LANDMARKS = {
    # Dehradun
    "clock tower, dehradun": (30.32432, 78.04186),
    "clock tower": (30.32432, 78.04186),
    "ghanta ghar, dehradun": (30.32432, 78.04186),
    "upes, dehradun": (30.41761, 77.96827),
    "upes bidholi campus, dehradun": (30.41761, 77.96827),
    "upes bidholi, dehradun": (30.41761, 77.96827),
    "upes kandoli campus, dehradun": (30.40455, 77.96918),
    "upes kandoli, dehradun": (30.40455, 77.96918),
    "pacific mall, rajpur road, dehradun": (30.36647, 78.06734),
    "pacific mall, dehradun": (30.36647, 78.06734),
    "isbt dehradun": (30.28688, 77.99845),
    "isbt, dehradun": (30.28688, 77.99845),
    "dehradun railway station": (30.31649, 78.03219),
    "ballupur chowk, dehradun": (30.33405, 78.00624),
    "ballupur, dehradun": (30.33405, 78.00624),
    "forest research institute (fri), dehradun": (30.34444, 78.00333),
    "fri, dehradun": (30.34444, 78.00333),
    "clement town, dehradun": (30.26781, 78.00693),
    "graphic era university, dehradun": (30.27301, 78.00762),
    "graphic era, dehradun": (30.27301, 78.00762),
    "dit university, dehradun": (30.39801, 78.07722),
    "rajpur road, dehradun": (30.35411, 78.06102),
    "jakhan, dehradun": (30.36015, 78.06452),
    "prem nagar, dehradun": (30.33754, 77.96022),
    "bidholi, dehradun": (30.41520, 77.96540),
    # Delhi
    "connaught place, delhi": (28.6315, 77.2167),
    "hauz khas village, delhi": (28.5535, 77.1945),
    "lajpat nagar central market, delhi": (28.5677, 77.2433),
    "lajpat nagar, delhi": (28.5677, 77.2433),
    "rajiv chowk metro station exit 2, delhi": (28.6328, 77.2197),
    "rajiv chowk, delhi": (28.6328, 77.2197),
    "chandni chowk market, delhi": (28.6506, 77.2303),
    "select citywalk mall, saket, delhi": (28.5283, 77.2185),
    "saket, delhi": (28.5283, 77.2185),
    "karol bagh main market, delhi": (28.6514, 77.1907),
    "india gate, delhi": (28.6129, 77.2295),
    "cyber hub, gurugram / delhi ncr": (28.4950, 77.0895),
    "aiims metro station, delhi": (28.5659, 77.2111),
    "khan market, delhi": (28.6002, 77.2273),
    "iit delhi main gate, delhi": (28.5450, 77.1926),
    # Mumbai
    "marine drive, mumbai": (18.9440, 72.8230),
    "bandra kurla complex (bkc), mumbai": (19.0660, 72.8680),
    "gateway of india, mumbai": (18.9220, 72.8347),
    "dadar railway station, mumbai": (19.0180, 72.8430),
    "andheri west metro station, mumbai": (19.1197, 72.8464),
    "juhu beach, mumbai": (19.0988, 72.8264),
    "colaba causeway, mumbai": (18.9150, 72.8280),
    "lower parel phoenix mall, mumbai": (18.9950, 72.8240),
    "nariman point, mumbai": (18.9260, 72.8210),
    # Bengaluru
    "mg road metro station, bengaluru": (12.9756, 77.6067),
    "indiranagar 100ft road, bengaluru": (12.9784, 77.6408),
    "koramangala 5th block, bengaluru": (12.9348, 77.6244),
    "whitefield main road, bengaluru": (12.9698, 77.7500),
    "electronic city phase 1, bengaluru": (12.8452, 77.6602),
    "commercial street, bengaluru": (12.9822, 77.6083),
    "majestic bus stand, bengaluru": (12.9778, 77.5714),
    "cubbon park entrance, bengaluru": (12.9760, 77.5930),
}

CITY_LANDMARKS_DB = {
    "dehradun": [
        "Clock Tower, Dehradun",
        "UPES Bidholi Campus, Dehradun",
        "UPES Kandoli Campus, Dehradun",
        "Pacific Mall, Rajpur Road, Dehradun",
        "ISBT Dehradun",
        "Dehradun Railway Station",
        "Forest Research Institute (FRI), Dehradun",
        "Ballupur Chowk, Dehradun",
        "Clement Town, Dehradun",
        "Graphic Era University, Dehradun",
        "DIT University, Dehradun",
        "Jakhan, Dehradun",
        "Prem Nagar, Dehradun",
    ],
    "delhi": [
        "Connaught Place, Delhi",
        "Hauz Khas Village, Delhi",
        "Lajpat Nagar Central Market, Delhi",
        "Rajiv Chowk Metro Station Exit 2, Delhi",
        "Chandni Chowk Market, Delhi",
        "Select Citywalk Mall, Saket, Delhi",
        "Karol Bagh Main Market, Delhi",
        "India Gate, Delhi",
        "Cyber Hub, Gurugram / Delhi NCR",
        "AIIMS Metro Station, Delhi",
        "Khan Market, Delhi",
        "IIT Delhi Main Gate, Delhi",
    ],
    "mumbai": [
        "Marine Drive, Mumbai",
        "Bandra Kurla Complex (BKC), Mumbai",
        "Gateway of India, Mumbai",
        "Dadar Railway Station, Mumbai",
        "Andheri West Metro Station, Mumbai",
        "Juhu Beach, Mumbai",
        "Colaba Causeway, Mumbai",
        "Lower Parel Phoenix Mall, Mumbai",
        "Nariman Point, Mumbai",
    ],
    "bengaluru": [
        "MG Road Metro Station, Bengaluru",
        "Indiranagar 100ft Road, Bengaluru",
        "Koramangala 5th Block, Bengaluru",
        "Whitefield Main Road, Bengaluru",
        "Electronic City Phase 1, Bengaluru",
        "Commercial Street, Bengaluru",
        "Majestic Bus Stand, Bengaluru",
        "Cubbon Park Entrance, Bengaluru",
    ],
}


def get_city_landmark_suggestions(city: str) -> List[str]:
    """Returns popular landmark suggestions for a given city."""
    if not city:
        return CITY_LANDMARKS_DB.get("dehradun", [])

    city_clean = city.strip().lower()
    for k, landmarks in CITY_LANDMARKS_DB.items():
        if k in city_clean or city_clean in k:
            return landmarks

    c_title = city.strip().title()
    return [
        f"Main Railway / Metro Station, {c_title}",
        f"City Center Market, {c_title}",
        f"Central Bus Terminal, {c_title}",
        f"Main Square / Clock Tower, {c_title}",
        f"University Campus, {c_title}",
        f"Shopping Mall, {c_title}",
    ]


@lru_cache(maxsize=500)
def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    High-Precision Multi-Stage Geocoder.
    Converts local address strings into exact (lat, lng) with memory caching.
    """
    if not address or not address.strip():
        return (None, None)

    address_clean = address.strip().lower()
    if address_clean in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[address_clean]

    # 1. Exact Match Table Check
    for k, coords in EXACT_LANDMARKS.items():
        if k in address_clean or address_clean in k:
            _GEOCODE_CACHE[address_clean] = coords
            return coords

    # 2. Multi-Stage Nominatim Search Queries
    queries = [
        address.strip(),
        f"{address.strip()}, India",
    ]
    
    # Clean common suffixes if specific search fails
    stripped = re.sub(r'\b(chowk|gate|campus|market|stand|exit \d+)\b', '', address_clean, flags=re.IGNORECASE).strip()
    if stripped and stripped != address_clean:
        queries.append(stripped)

    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "SafeWalk_Precision_Geocoder/2.0"}

    for q in queries:
        try:
            time.sleep(0.05)
            params = {"q": q, "format": "json", "limit": 1}
            res = requests.get(url, params=params, headers=headers, timeout=3.5).json()
            if res and isinstance(res, list) and len(res) > 0:
                lat = float(res[0]["lat"])
                lng = float(res[0]["lon"])
                _GEOCODE_CACHE[address_clean] = (lat, lng)
                return (lat, lng)
        except Exception as e:
            pass

    # 3. City Defaults Fallback
    city_defaults = {
        "dehradun": (30.3243, 78.0419),
        "delhi": (28.6139, 77.2090),
        "mumbai": (19.0760, 72.8777),
        "bengaluru": (12.9716, 77.5946),
        "kolkata": (22.5726, 88.3639),
        "chennai": (13.0827, 80.2707),
        "hyderabad": (17.3850, 78.4867),
        "tokyo": (35.6762, 139.6503),
        "london": (51.5074, -0.1278),
        "paris": (48.8566, 2.3522),
        "new york": (40.7128, -74.0060),
        "lagos": (6.5244, 3.3792),
        "dubai": (25.2048, 55.2708),
        "singapore": (1.3521, 103.8198),
        "sydney": (-33.8688, 151.2093),
        "berlin": (52.5200, 13.4050),
    }

    for c_key, coords in city_defaults.items():
        if c_key in address_clean:
            _GEOCODE_CACHE[address_clean] = coords
            return coords

    return (None, None)


@lru_cache(maxsize=500)
def get_city_country_from_coords(lat: float, lng: float) -> Tuple[str, str]:
    """Reverse geocodes coordinates to (city, country)."""
    cache_key = f"{round(lat, 3)},{round(lng, 3)}"
    if cache_key in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[cache_key]

    url = "https://nominatim.openstreetmap.org/reverse"
    headers = {"User-Agent": "SafeWalk_Precision_Geocoder/2.0"}
    params = {"lat": lat, "lon": lng, "format": "json"}

    try:
        time.sleep(0.05)
        res = requests.get(url, params=params, headers=headers, timeout=3.5).json()
        if res and isinstance(res, dict):
            addr = res.get("address", {})
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state_district") or "Delhi"
            country = addr.get("country") or "India"
            _GEOCODE_CACHE[cache_key] = (city, country)
            return (city, country)
    except Exception as e:
        print(f"Reverse geocode exception for ({lat}, {lng}): {e}")

    return ("Delhi", "India")
