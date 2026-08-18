# geocoder.py — MEMBER 2 OWNS THIS FILE
import requests


def geocode_address(address):
    if not address or not str(address).strip():
        return (None, None)
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(str(address))}&format=json&limit=1"
        headers = {'User-Agent': 'SafeWalk/2.0'}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200 and len(r.json()) > 0:
            data = r.json()[0]
            return float(data['lat']), float(data['lon'])
    except Exception:
        pass
    # Fallback to Delhi default coordinates if Nominatim API is unavailable
    return (28.6139, 77.2090)


def get_city_country_from_coords(lat, lng):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {'User-Agent': 'SafeWalk/2.0'}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            address = r.json().get('address', {})
            city = address.get('city') or address.get('town') or address.get('state') or 'Delhi'
            country = address.get('country') or 'India'
            return city, country
    except Exception:
        pass
    return 'Delhi', 'India'
