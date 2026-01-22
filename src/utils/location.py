from geopy.geocoders import Nominatim
from typing import Optional, Tuple

def get_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """Get latitude and longitude from a location string."""
    geolocator = Nominatim(user_agent="astra_astrology")
    try:
        result = geolocator.geocode(location)
        if result:
            return result.latitude, result.longitude
        return None
    except Exception as e:
        print(f"Geocoding failed: {e}")
        return None

# # Example
# result = get_coordinates("Mumbai, India")
# if result:
#     lat, lon = result
#     print(f"Latitude: {lat}, Longitude: {lon}")
# else:
#     print("Could not get coordinates")