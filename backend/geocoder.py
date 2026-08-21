# geocoder.py - High-Precision Multi-Stage Geocoder & City Landmark Engine
import requests
import re
import time
from functools import lru_cache
from typing import Tuple, Optional, List

_GEOCODE_CACHE = {}

# Pre-indexed exact GPS coordinates for popular city landmarks
EXACT_LANDMARKS = {
    # Dehradun
    "clock tower, dehradun": (30.32433, 78.04191),
    "upes bidholi campus, dehradun": (30.41520, 77.96540),
    "upes bidholi, dehradun": (30.41520, 77.96540),
    "upes kandoli campus, dehradun": (30.40210, 77.96800),
    "upes kandoli, dehradun": (30.40210, 77.96800),
    "pacific mall, rajpur road, dehradun": (30.36020, 78.06780),
    "pacific mall, dehradun": (30.36020, 78.06780),
    "isbt dehradun": (30.28710, 77.99720),
    "dehradun railway station": (30.31650, 78.03220),
    "forest research institute (fri), dehradun": (30.34290, 78.00060),
    "fri, dehradun": (30.34290, 78.00060),
    "ballupur chowk, dehradun": (30.33470, 78.01250),
    "clement town, dehradun": (30.26810, 78.00710),
    "graphic era university, dehradun": (30.26860, 78.00620),
    "dit university, dehradun": (30.39800, 78.07500),
    "jakhan, dehradun": (30.36210, 78.06820),
    "prem nagar, dehradun": (30.33754, 77.96022),
    "bidholi, dehradun": (30.41520, 77.96540),
    
    # Delhi
    "connaught place, delhi": (28.6315, 77.2167),
    "hauz khas village, delhi": (28.5535, 77.1945),
    "lajpat nagar central market, delhi": (28.5677, 77.2433),
    "rajiv chowk metro station exit 2, delhi": (28.6328, 77.2197),
    "chandni chowk market, delhi": (28.6506, 77.2303),
    "select citywalk mall, saket, delhi": (28.5283, 77.2185),
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

    # Kolkata
    "park street, kolkata": (22.5552, 88.3518),
    "howrah railway station, kolkata": (22.5840, 88.3426),
    "victoria memorial, kolkata": (22.5448, 88.3426),
    "salt lake sector 5, kolkata": (22.5726, 88.4332),
    "new market, kolkata": (22.5601, 88.3526),
    "esplanade metro station, kolkata": (22.5647, 88.3516),

    # Chennai
    "t nagar ranganathan street, chennai": (13.0405, 80.2337),
    "marina beach promenade, chennai": (13.0500, 80.2824),
    "anna nagar main road, chennai": (13.0850, 80.2101),
    "chennai central railway station, chennai": (13.0827, 80.2755),
    "nungambakkam high road, chennai": (13.0601, 80.2407),
    "express avenue mall, royapettah, chennai": (13.0587, 80.2642),

    # Hyderabad
    "hitech city mindspace, hyderabad": (17.4435, 78.3772),
    "charminar main market, hyderabad": (17.3616, 78.4747),
    "gachibowli dlf cybercity, hyderabad": (17.4474, 78.3565),
    "jubilee hills checkpost, hyderabad": (17.4325, 78.4071),
    "secunderabad railway station, hyderabad": (17.4344, 78.5013),
    "inorbit mall, madhapur, hyderabad": (17.4375, 78.3885),

    # Tokyo
    "shibuya crossing, tokyo": (35.6595, 139.7004),
    "shinjuku station east exit, tokyo": (35.6909, 139.7003),
    "ginza six shopping district, tokyo": (35.6696, 139.7640),
    "akihabara electric town, tokyo": (35.6997, 139.7711),
    "roppongi hills, tokyo": (35.6605, 139.7292),
    "asakusa sensoji temple, tokyo": (35.7148, 139.7967),

    # London
    "oxford circus, london": (51.5152, -0.1419),
    "piccadilly circus, london": (51.5101, -0.1342),
    "covent garden market, london": (51.5117, -0.1240),
    "soho square, london": (51.5150, -0.1320),
    "king's cross st pancras station, london": (51.5309, -0.1238),
    "trafalgar square, london": (51.5080, -0.1281),

    # Paris
    "champs-élysées avenue, paris": (48.8698, 2.3075),
    "eiffel tower plaza, paris": (48.8584, 2.2945),
    "le marais quarter, paris": (48.8570, 2.3590),
    "châtelet–les halles station, paris": (48.8622, 2.3470),
    "saint-germain-des-prés, paris": (48.8538, 2.3333),
    "montmartre sacré-cœur, paris": (48.8867, 2.3431),

    # New York
    "times square, new york": (40.7580, -73.9855),
    "grand central terminal, new york": (40.7527, -73.9772),
    "union square, new york": (40.7359, -73.9911),
    "washington square park, greenwich village, new york": (40.7308, -73.9973),
    "herald square macy's, new york": (40.7508, -73.9890),
    "soho broadway shopping district, new york": (40.7233, -74.0030),

    # Lagos
    "victoria island commercial hub, lagos": (6.4281, 3.4219),
    "lekki phase 1 admiral way, lagos": (6.4474, 3.4723),
    "ikoyi kingsway road, lagos": (6.4520, 3.4380),
    "ikeja city mall, lagos": (6.6136, 3.3582),
    "marina cms bus terminal, lagos": (6.4531, 3.3886),

    # Dubai
    "dubai mall main entrance, dubai": (25.1972, 55.2797),
    "downtown dubai boulevard, dubai": (25.1950, 55.2780),
    "dubai marina walk, dubai": (25.0772, 55.1332),
    "mall of the emirates, dubai": (25.1181, 55.2006),
    "deira city centre, dubai": (25.2517, 55.3331),
    "business bay metro station, dubai": (25.1912, 55.2662),

    # Singapore
    "orchard road ion station, singapore": (1.3040, 103.8320),
    "marina bay sands promenade, singapore": (1.2838, 103.8591),
    "clarke quay riverside, singapore": (1.2905, 103.8462),
    "bugis street market, singapore": (1.3008, 103.8550),
    "raffles place financial hub, singapore": (1.2839, 103.8515),
    "chinatown pagoda street, singapore": (1.2835, 103.8442),
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
    "kolkata": [
        "Park Street, Kolkata",
        "Howrah Railway Station, Kolkata",
        "Victoria Memorial, Kolkata",
        "Salt Lake Sector 5, Kolkata",
        "New Market, Kolkata",
        "Esplanade Metro Station, Kolkata",
    ],
    "chennai": [
        "T Nagar Ranganathan Street, Chennai",
        "Marina Beach Promenade, Chennai",
        "Anna Nagar Main Road, Chennai",
        "Chennai Central Railway Station, Chennai",
        "Nungambakkam High Road, Chennai",
        "Express Avenue Mall, Royapettah, Chennai",
    ],
    "hyderabad": [
        "HITECH City Mindspace, Hyderabad",
        "Charminar Main Market, Hyderabad",
        "Gachibowli DLF Cybercity, Hyderabad",
        "Jubilee Hills Checkpost, Hyderabad",
        "Secunderabad Railway Station, Hyderabad",
        "Inorbit Mall, Madhapur, Hyderabad",
    ],
    "tokyo": [
        "Shibuya Crossing, Tokyo",
        "Shinjuku Station East Exit, Tokyo",
        "Ginza Six Shopping District, Tokyo",
        "Akihabara Electric Town, Tokyo",
        "Roppongi Hills, Tokyo",
        "Asakusa Sensoji Temple, Tokyo",
    ],
    "london": [
        "Oxford Circus, London",
        "Piccadilly Circus, London",
        "Covent Garden Market, London",
        "Soho Square, London",
        "King's Cross St Pancras Station, London",
        "Trafalgar Square, London",
    ],
    "paris": [
        "Champs-Élysées Avenue, Paris",
        "Eiffel Tower Plaza, Paris",
        "Le Marais Quarter, Paris",
        "Châtelet–Les Halles Station, Paris",
        "Saint-Germain-des-Prés, Paris",
        "Montmartre Sacré-Cœur, Paris",
    ],
    "new york": [
        "Times Square, New York",
        "Grand Central Terminal, New York",
        "Union Square, New York",
        "Washington Square Park, Greenwich Village, New York",
        "Herald Square Macy's, New York",
        "SoHo Broadway Shopping District, New York",
    ],
    "lagos": [
        "Victoria Island Commercial Hub, Lagos",
        "Lekki Phase 1 Admiral Way, Lagos",
        "Ikoyi Kingsway Road, Lagos",
        "Ikeja City Mall, Lagos",
        "Marina CMS Bus Terminal, Lagos",
    ],
    "dubai": [
        "Dubai Mall Main Entrance, Dubai",
        "Downtown Dubai Boulevard, Dubai",
        "Dubai Marina Walk, Dubai",
        "Mall of the Emirates, Dubai",
        "Deira City Centre, Dubai",
        "Business Bay Metro Station, Dubai",
    ],
    "singapore": [
        "Orchard Road ION Station, Singapore",
        "Marina Bay Sands Promenade, Singapore",
        "Clarke Quay Riverside, Singapore",
        "Bugis Street Market, Singapore",
        "Raffles Place Financial Hub, Singapore",
        "Chinatown Pagoda Street, Singapore",
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
