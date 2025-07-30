

#Reverse‑geocode latitude/longitude into city & state using Google Maps API.
"""
Example:
    from location import reverse_geocode, get_city_state
    print(reverse_geocode(26.4499, 80.3319))
"""

import os
from typing import Dict, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


class GeocodeError(Exception):
    """Custom error when reverse geocoding fails."""
    pass


def _extract_component(components: list, component_type: str) -> str:
    # Finds and returns the value for a specific component type (e.g., 'locality', 'state')
    for comp in components:
        if component_type in comp.get("types", []):
            return comp.get("long_name", "")
    return ""


def reverse_geocode(lat: float, lon: float) -> Dict[str, str]:
    
    #Returns city, state, and country for the given coordinates.
    #Raises GeocodeError if lookup fails.
    
    if not GOOGLE_API_KEY:
        raise GeocodeError("GOOGLE_API_KEY missing in environment variables")

    params = {"latlng": f"{lat},{lon}", "key": GOOGLE_API_KEY}
    try:
        resp = requests.get(GEOCODE_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except (requests.exceptions.RequestException, ValueError) as exc:
        raise GeocodeError(f"Request error: {exc}") from exc

    if data.get("status") != "OK" or not data.get("results"):
        raise GeocodeError(f"Geocoding failed: {data.get('status')}")

    # Pull from the first (most relevant) address result
    components = data["results"][0]["address_components"]
    city = (
        _extract_component(components, "locality")
        or _extract_component(components, "administrative_area_level_2")
    )
    state = _extract_component(components, "administrative_area_level_1")
    country = _extract_component(components, "country")

    if not city or not state:
        raise GeocodeError("Could not parse city/state from response")

    return {"city": city, "state": state, "country": country}


def get_city_state(lat: float, lon: float) -> Tuple[str, str]:
    # Just returns city and state as a tuple
    place = reverse_geocode(lat, lon)
    return place["city"], place["state"]


if __name__ == "__main__":
    # Test locally by running this file directly
    sample_lat, sample_lon = 26.4499, 80.3319
    try:
        print(reverse_geocode(sample_lat, sample_lon))
    except GeocodeError as e:
        print("Error:", e)
