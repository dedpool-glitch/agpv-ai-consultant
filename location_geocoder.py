from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def geocode_location(location_text):
    if not location_text.strip():
        raise ValueError("Location cannot be empty.")
    
    geolocator=Nominatim(user_agent="agpv_ai_consultant")
    try:
        location=geolocator.geocode(location_text,timeout=10)
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        raise RuntimeError(f"Geocoding service is currently unavailable: {e}") from e
    
    if location is None:
        raise ValueError(f"Could not retrieve coordinates for this location: '{location_text}'.")
    
    return {"latitude": location.latitude, "longitude": location.longitude, "address": location.address}