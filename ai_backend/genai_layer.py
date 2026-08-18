"""
Gemini GenAI Layer for SafeWalk
Handles Route Briefing, NLP Incident Extraction, Emergency SOS Message Generation, and City Overviews.
"""

import os
import json
import re
import google.generativeai as genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_api_key():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                        return v.strip("'\" ")
    return "YOUR_GEMINI_KEY"

API_KEY = get_api_key()
genai.configure(api_key=API_KEY)

# Use valid active Gemini Flash model name
model = genai.GenerativeModel('gemini-1.5-flash-latest')


def generate_safety_briefing(route_data: any, time_str: str, city: str = "Delhi", country: str = "India", verified_reports: int = 0, recent_reports: int = 0) -> str:
    """
    Generates a 5-bullet route safety briefing.
    Falls back gracefully to professional safety guidance if API is unavailable.
    """
    avg_score = route_data.get("average", route_data) if isinstance(route_data, dict) else route_data
    if isinstance(avg_score, (int, float)):
        avg_score = round(avg_score)
    else:
        avg_score = 75

    prompt = f"""
Act as a personal safety expert for pedestrians and women in {city}, {country}.
Time of Travel: {time_str}
Route Safety Score: {avg_score}/100
City Incident Data: {verified_reports} verified community reports, {recent_reports} reports in last 24h.

Provide EXACTLY 5 concise bullet points of actionable safety advice for walking this route in {city} at {time_str}.
Keep each bullet concise and practical.
"""
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"Gemini briefing fallback: {e}")

    # Professional 5-bullet fallback briefing
    return (
        f"• 🟢 Route Safety Score for {city}: {avg_score}/100 at {time_str}.\n"
        f"• 💡 Stick to well-lit main arterial roads and avoid unlit alleyways or shortcuts.\n"
        f"• 📱 Keep your mobile phone charged, GPS active, and emergency SOS contacts accessible.\n"
        f"• 👥 Walk confidently near active storefronts, transit hubs, and populated commercial areas.\n"
        f"• 🚨 Report any suspicious activity or unsafe conditions to local authorities and the SafeWalk community."
    )


def process_incident_report(report_text: str, city: str = "Delhi", country: str = "India") -> dict:
    """Parses plain text report into structured JSON using Gemini NLP."""
    prompt = f"""
Analyze this incident report from a user in {city}, {country}:
"{report_text}"

Extract the details and return ONLY a JSON object (no markdown, no backticks):
{{
  "location_description": "specific location mentioned, or '{city}'",
  "incident_type": "harassment/following/theft/unsafe_area",
  "severity": 1, 2, or 3,
  "time_of_day": "night/evening/afternoon/morning",
  "confidence": 0.0 to 1.0
}}
severity: 1=uncomfortable, 2=threatened, 3=attacked/stalked
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception as e:
        print(f"NLP parser fallback: {e}")
        return {
            "location_description": city,
            "incident_type": "unsafe_area",
            "severity": 2,
            "time_of_day": "night",
            "confidence": 0.6
        }


def generate_sos_message(user_name: str, current_loc: str, dest_loc: str, city: str = "Delhi") -> str:
    """Generates a concise 160-char SMS emergency message."""
    prompt = f"""
Write a 160-character emergency SMS from {user_name} walking in {city}.
Current Location: {current_loc}
Destination: {dest_loc}
Include urgent help call, coordinates/location, and request to check live location.
"""
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()[:160]
    except Exception as e:
        print(f"SOS generator fallback: {e}")

    return f"EMERGENCY SOS: I am {user_name} walking near {current_loc} heading to {dest_loc} in {city}. Please check on me or call police immediately!"[:160]


def get_city_safety_overview(city: str = "Delhi") -> str:
    """Generates high-level city safety summary."""
    prompt = f"Provide a brief 3-sentence pedestrian and women safety overview for {city} during night hours."
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"City overview fallback: {e}")

    return f"{city} has varying pedestrian safety depending on time and area. Stick to main roads, stay near active commercial areas, and keep emergency contacts ready."
