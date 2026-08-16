# geocoder.py — MEMBER 2 OWNS THIS FILE
import requests
from typing import Tuple, Optional

CACHE_GEOCODE = {}
CACHE_REVERSE = {}

def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocodes an address string to (lat, lng) using OpenStreetMap Nominatim API.
    Supports any city worldwide with caching and offline fallback for reliability.
    """
    if not address or not address.strip():
        return None, None

    clean_addr = address.strip().lower()
    if clean_addr in CACHE_GEOCODE:
        return CACHE_GEOCODE[clean_addr]

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "accept-language": "en"
    }
    headers = {
        "User-Agent": "SafeWalk-App/2.0 (hackathon-demo-upes@safewalk.org)",
        "Accept-Language": "en"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                CACHE_GEOCODE[clean_addr] = (lat, lng)
                return lat, lng
    except Exception:
        pass

    # Built-in fallbacks for common demo locations in case of offline / rate limits
    known_locations = {
        "connaught place": (28.6315, 77.2167),
        "connaught place, delhi": (28.6315, 77.2167),
        "lajpat nagar": (28.5677, 77.2433),
        "lajpat nagar, delhi": (28.5677, 77.2433),
        "delhi": (28.6139, 77.2090),
        "new delhi": (28.6139, 77.2090),
        "hauz khas": (28.5535, 77.1945),
        "hauz khas village": (28.5535, 77.1945),
        "chandni chowk": (28.6506, 77.2303),
        "saket": (28.5283, 77.2185),
        "shibuya station, tokyo": (35.6580, 139.7016),
        "shibuya station tokyo": (35.6580, 139.7016),
        "shinjuku station, tokyo": (35.6896, 139.7006),
        "shinjuku station tokyo": (35.6896, 139.7006),
        "harajuku, tokyo": (35.6702, 139.7027),
        "harajuku tokyo": (35.6702, 139.7027),
        "tokyo": (35.6762, 139.6503),
        "london": (51.5074, -0.1278),
        "lagos": (6.5244, 3.3792),
        "new york": (40.7128, -74.0060),
    }

    for k, coords in known_locations.items():
        if k in clean_addr or clean_addr in k:
            CACHE_GEOCODE[clean_addr] = coords
            return coords

    return None, None

def get_city_country_from_coords(lat: float, lng: float) -> Tuple[str, str]:
    """
    Reverse geocodes (lat, lng) to (city, country) using Nominatim OpenStreetMap.
    """
    if lat is None or lng is None:
        return "Unknown", "Unknown"

    cache_key = (round(lat, 3), round(lng, 3))
    if cache_key in CACHE_REVERSE:
        return CACHE_REVERSE[cache_key]

    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json",
        "accept-language": "en"
    }
    headers = {
        "User-Agent": "SafeWalk-App/2.0 (hackathon-demo-upes@safewalk.org)",
        "Accept-Language": "en"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            address = data.get("address", {})
            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("state_district")
                or address.get("suburb")
                or address.get("city_district")
                or address.get("county")
                or address.get("state")
                or "Unknown City"
            )
            country = address.get("country", "Unknown")
            CACHE_REVERSE[cache_key] = (city, country)
            return city, country
    except Exception:
        pass

    # Heuristic fallback based on geographical bounds
    if 28.3 <= lat <= 28.9 and 76.8 <= lng <= 77.5:
        res = ("Delhi", "India")
    elif 35.4 <= lat <= 35.9 and 139.4 <= lng <= 140.1:
        res = ("Tokyo", "Japan")
    elif 51.2 <= lat <= 51.8 and -0.6 <= lng <= 0.4:
        res = ("London", "United Kingdom")
    elif 6.2 <= lat <= 6.8 and 3.1 <= lng <= 3.7:
        res = ("Lagos", "Nigeria")
    elif 40.5 <= lat <= 40.9 and -74.3 <= lng <= -73.7:
        res = ("New York", "United States")
    else:
        res = ("City", "Global")

    CACHE_REVERSE[cache_key] = res
    return res
