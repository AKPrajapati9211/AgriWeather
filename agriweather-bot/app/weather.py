
#Fetches weather forecast using OpenWeatherMap API.
"""
Example:
    from weather import get_weather_forecast
    forecast = get_weather_forecast("Kanpur")
    print(forecast)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

API_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherAPIError(Exception):
    """Raised when weather API fails."""
    pass


def get_weather_forecast(city_name: str) -> dict:
    """
    Returns average temperature, total rainfall, and description
    for the next 24 hours (8 × 3-hour slots).
    """
    if not WEATHER_API_KEY:
        raise WeatherAPIError("WEATHER_API_KEY missing in environment variables")

    params = {
        "q": city_name,
        "appid": WEATHER_API_KEY,
        "units": "metric",
        "cnt": 8  # 3-hour forecast × 8 = 24 hours
    }

    try:
        res = requests.get(API_URL, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()
    except requests.RequestException as exc:
        raise WeatherAPIError(f"Request failed: {exc}") from exc

    if data.get("cod") != "200":
        raise WeatherAPIError(f"API error: {data.get('message')}")

    total_temp = 0
    total_rain = 0
    descriptions = []

    # Go through each 3-hour forecast
    for entry in data["list"]:
        total_temp += entry["main"]["temp"]
        total_rain += entry.get("rain", {}).get("3h", 0)
        descriptions.append(entry["weather"][0]["description"])

    avg_temp = total_temp / len(data["list"])

    return {
        "temperature": round(avg_temp, 1),
        "rain": round(total_rain, 1),
        "description": max(set(descriptions), key=descriptions.count)  # Most common description
    }


if __name__ == "__main__":
    # Simple manual test for Kanpur
    try:
        forecast = get_weather_forecast("Kanpur")
        print("🌦️ Forecast for Kanpur:")
        print(forecast)
    except WeatherAPIError as e:
        print("❌ Error:", e)
