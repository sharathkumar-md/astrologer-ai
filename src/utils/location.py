from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Optional, Tuple
import re

# Fallback coordinates for common Indian cities (when Nominatim fails)
_CITY_FALLBACKS = {
    "visakhapatnam": (17.7312, 83.3010),
    "vizag": (17.7312, 83.3010),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.7041, 77.1025),
    "new delhi": (28.6139, 77.2090),
    "chennai": (13.0827, 80.2707),
    "bangalore": (12.9716, 77.5946),
    "bengaluru": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "kanpur": (26.4499, 80.3319),
    "nagpur": (21.1458, 79.0882),
    "indore": (22.7196, 75.8577),
    "kochi": (9.9312, 76.2673),
    "cochin": (9.9312, 76.2673),
    "thiruvananthapuram": (8.5241, 76.9366),
    "trivandrum": (8.5241, 76.9366),
}


def _normalize_for_lookup(s: str) -> str:
    """Lowercase and strip for lookup."""
    return re.sub(r"\s+", " ", s.strip().lower())

def get_coordinates(location: str) -> Optional[Tuple[float, float]]:
   """Get latitude and longitude from a location string.
    Uses fallback list first for common Indian cities, then Nominatim.
    """
    if not location or not location.strip():
        return None
    loc = location.strip()
    loc_lower = _normalize_for_lookup(loc)

    # 1) Fallback first: city part before comma (e.g. "Mumbai, India" -> "mumbai")
    city_part = loc_lower.split(",")[0].strip()
    if city_part in _CITY_FALLBACKS:
        return _CITY_FALLBACKS[city_part]
    # First word only (e.g. "New Delhi, India" -> "new" won't match; "Mumbai" -> "mumbai" already matched above)
    first_word = city_part.split()[0] if city_part else ""
    if first_word in _CITY_FALLBACKS:
        return _CITY_FALLBACKS[first_word]
    # 2) Any fallback city name contained in the full string
    for city_name, coords in _CITY_FALLBACKS.items():
        if city_name in loc_lower:
            return coords

    # 3) Try Nominatim
    geolocator = Nominatim(user_agent="astra_astrology", timeout=10)
    queries_to_try = [loc]
    if "," in loc:
        queries_to_try.append(loc.split(",")[0].strip())
    for query in queries_to_try:
        if not query:
            continue
        try:
            result = geolocator.geocode(query)
            if result:
                return result.latitude, result.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            continue
        except Exception:
            continue

    return None

# # Example
# result = get_coordinates("Mumbai, India")
# if result:
#     lat, lon = result
#     print(f"Latitude: {lat}, Longitude: {lon}")
# else:
#     print("Could not get coordinates")
