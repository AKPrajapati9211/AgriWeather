
#Checks whether the weather forecast is suitable for a specific crop stage.


import json
import os
from datetime import datetime

CROP_DATA_FILE = os.path.join(os.path.dirname(__file__), "crop_data.json")


class CropAdviceError(Exception):
    """Custom error for crop-related advice issues."""
    pass


def load_crop_data() -> dict:
    if not os.path.exists(CROP_DATA_FILE):
        raise CropAdviceError("❌ crop_data.json not found.")
    try:
        with open(CROP_DATA_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise CropAdviceError("❌ crop_data.json is not valid JSON.")


def generate_advice(crop_name: str, forecast: dict, stage: str = "sowing") -> str:
    crop_data = load_crop_data()
    crop_name = crop_name.lower()
    stage = stage.lower()

    if crop_name not in crop_data:
        raise CropAdviceError(f"❌ No data available for crop: '{crop_name.title()}'")

    if stage not in crop_data[crop_name]:
        raise CropAdviceError(f"❌ Stage '{stage}' not found for crop '{crop_name.title()}'")

    crop_stage = crop_data[crop_name][stage]
    temp = forecast["temperature"]
    rain = forecast["rain"]
    desc = forecast["description"]

    current_month = datetime.now().month
    month_range = crop_stage.get("months", [])
    month_ok = True

    if len(month_range) == 2:
        start_month, end_month = month_range
        if start_month <= end_month:
            month_ok = start_month <= current_month <= end_month
        else:
            month_ok = current_month >= start_month or current_month <= end_month

    temp_ok = crop_stage["temp_min"] <= temp <= crop_stage["temp_max"]
    rain_ok = crop_stage["rain_min"] <= rain <= crop_stage["rain_max"]

    result = f"🌾 *Crop:* {crop_name.title()} ({stage.title()} Stage)\n"

    if len(month_range) == 2:
        result += f"🗓️ Ideal Months: {month_name(start_month)} to {month_name(end_month)}\n"
        result += f"📅 Current: {month_name(current_month)} ({'✅ OK' if month_ok else '⚠️ Not ideal'})\n"

    result += f"🌡️ Temp: {temp}°C ({'✅ OK' if temp_ok else '⚠️ Out of range'})\n"
    result += f"🌧️ Rain: {rain} mm ({'✅ OK' if rain_ok else '⚠️ Out of range'})\n"
    result += f"🌤️ Weather: {desc}\n"

    if temp_ok and rain_ok and month_ok:
        result += "\n✅ Weather and timing are *suitable* for this crop stage!"
    else:
        result += "\n⚠️ One or more conditions are not ideal. Please be cautious."

    return result


def month_name(month_num: int) -> str:
    try:
        return datetime(2025, month_num, 1).strftime("%B")
    except:
        return f"Month {month_num}"
