from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os

from location import reverse_geocode, GeocodeError
from weather import get_weather_forecast, WeatherAPIError
from crop_advice import generate_advice, CropAdviceError

load_dotenv()
app = Flask(__name__)

user_sessions = {}

@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    sender = request.values.get("From", "")
    incoming_msg = request.values.get("Body", "").strip().lower()
    latitude = request.values.get("Latitude")
    longitude = request.values.get("Longitude")

    response = MessagingResponse()
    msg = response.message()

    print(f"From: {sender}")
    print(f"Message: {incoming_msg}")
    print(f"Latitude: {latitude}, Longitude: {longitude}")

    # Step 0: Restart if user types 'hi' at any stage
    if incoming_msg in ["hi", "start", "restart"]:
        user_sessions.pop(sender, None)
        user_sessions[sender] = {"stage": "awaiting_crop"}
        msg.body("""👋 Welcome!
    Please enter your *crop and stage* in one message.
    Example: `wheat, s` or `rice, harvesting`""")
        return str(response)

    if sender in user_sessions:
        session = user_sessions[sender]

        # Step 1: Accept crop and stage (combined or separate)
        if session["stage"] == "awaiting_crop":
            parts = [p.strip() for p in incoming_msg.split(",")]

            if len(parts) == 2:
                crop = parts[0]
                stage_input = parts[1]

                if stage_input in ["s", "sowing"]:
                    stage = "sowing"
                elif stage_input in ["h", "harvesting"]:
                    stage = "harvesting"
                else:
                    msg.body("⚠️ Please use `s` for sowing or `h` for harvesting.\nExample: wheat, s")
                    return str(response)

                session["crop"] = crop
                session["stage_type"] = stage
                session["stage"] = "awaiting_location"
                msg.body(f"📍 Got it!\nCrop: *{crop.title()}*, Stage: *{stage.title()}*\nNow please share your *location* using the 📎 attachment.")
                return str(response)

            else:
                session["crop"] = incoming_msg
                session["stage"] = "awaiting_stage"
                msg.body("🌀 Please enter the stage: `sowing` or `harvesting` (or `s` / `h`).")
                return str(response)

        # Step 2: Accept stage after crop
        elif session["stage"] == "awaiting_stage":
            if incoming_msg in ["s", "sowing"]:
                stage = "sowing"
            elif incoming_msg in ["h", "harvesting"]:
                stage = "harvesting"
            else:
                msg.body("⚠️ Invalid stage. Please reply with `sowing`, `harvesting`, `s`, or `h`.")
                return str(response)

            session["stage_type"] = stage
            session["stage"] = "awaiting_location"
            msg.body("📍 Noted. Now share your *location* using the 📎 attachment in WhatsApp.")
            return str(response)

        # Step 3: Handle location
        elif session["stage"] == "awaiting_location":
            if not latitude or not longitude:
                msg.body("⚠️ Location not detected. Please *share your live location* using the 📎 button.")
                return str(response)

            try:
                lat = float(latitude)
                lon = float(longitude)
            except ValueError:
                msg.body("⚠️ Invalid location format. Please share location again.")
                return str(response)

            try:
                location_data = reverse_geocode(lat, lon)
                city = location_data["city"]
                state = location_data["state"]
            except GeocodeError as e:
                msg.body(f"❌ Location error: {e}")
                return str(response)

            try:
                forecast = get_weather_forecast(city)
            except WeatherAPIError as e:
                msg.body(f"⚠️ Unable to fetch weather for {city}: {e}")
                return str(response)

            try:
                crop = session["crop"]
                stage_type = session["stage_type"]
                advice = generate_advice(crop, forecast, stage=stage_type)
            except CropAdviceError as e:
                msg.body(f"❌ {e}")
                return str(response)

            final_msg = (
                f"📍 *Location:* {city}, {state}\n"
                f"🌾 *Crop:* {crop.title()} ({stage_type.title()} stage)\n\n"
                f"{advice}"
            )
            msg.body(final_msg)
            user_sessions.pop(sender, None)
            return str(response)

    # Fallback for unrecognized input
    msg.body("🙋 Type *Hi* to start getting crop-weather advice.\nExample: `rice, sowing` or `tomato, h`")
    return str(response)

if __name__ == "__main__":
    app.run(debug=True)