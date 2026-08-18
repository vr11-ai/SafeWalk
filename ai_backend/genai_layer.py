# genai_layer.py — MEMBER 1 OWNS THIS FILE (4 Gemini Features, City-Aware, Real-Time Aware)
import os
import json
import re

try:
    import google.generativeai as genai
    api_key = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_KEY')
    if api_key != 'YOUR_GEMINI_KEY':
        genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False


# FEATURE 1 — Route Safety Briefing
def generate_safety_briefing(route_data, time_str, city, country, verified_reports=0, recent_reports=0):
    realtime_ctx = ''
    if recent_reports > 0:
        realtime_ctx = f'{recent_reports} reports in last 24h. {verified_reports} verified by community.'
    else:
        realtime_ctx = 'No recent reports in this area.'

    score = route_data.get("average", 70) if isinstance(route_data, dict) else 70

    prompt = f'''
You are SafeWalk safety advisor for women in {city}, {country}.
Safety score: {score}/100
Time: {time_str}
Real-time data: {realtime_ctx}

Give exactly 5 bullet points:
1. One-line route assessment at this time
2. City-specific safety context for {city}
3. What to do if unsafe (include local emergency number)
4. Take this route or use transport?
5. One empowering tip specific to {city}

Tone: Direct, respectful. NOT fearmongering. Under 150 words.
'''
    if HAS_GENAI and os.environ.get('GEMINI_API_KEY'):
        try:
            return model.generate_content(prompt).text
        except Exception:
            pass

    return (
        f"1. SafeWalk assessment for {city}: Primary route safety score is {score}/100.\n"
        f"2. Context: {realtime_ctx}\n"
        f"3. Emergency info: Dial 112 for local emergency services in {city}, {country}.\n"
        f"4. Transit recommendation: Prefer well-lit main thoroughfares during evening hours.\n"
        f"5. Safety tip: Stay alert, walk confidently, and keep family updated via SOS alert."
    )


# FEATURE 2 — Incident Report NLP (extracts structure from free text)
def process_incident_report(user_text, city, country):
    prompt = f'''
Extract incident details from this report.
Reporter is in: {city}, {country}
Report: "{user_text}"

Return ONLY valid JSON:
{{
 "location_description": "specific place mentioned",
 "incident_type": "harassment/following/theft/unsafe_area/other",
 "time_of_day": "morning/afternoon/evening/night/unknown",
 "severity": 1,
 "confidence": 0.0
}}

severity: 1=uncomfortable 2=threatened 3=attacked
confidence: 0.0-1.0 how clearly location is described
'''
    if HAS_GENAI and os.environ.get('GEMINI_API_KEY'):
        try:
            resp = model.generate_content(prompt).text
            match = re.search(r'\{.*\}', resp, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

    # Fallback keyword parser
    lower_text = str(user_text).lower()
    sev = 3 if any(w in lower_text for w in ['attacked', 'assault', 'weapon', 'danger']) else 2 if any(w in lower_text for w in ['followed', 'harassed', 'chased']) else 1
    inc_type = 'harassment' if 'harass' in lower_text or 'followed' in lower_text else 'theft' if 'stole' in lower_text or 'theft' in lower_text else 'unsafe_area'
    
    return {
        "location_description": user_text[:60],
        "incident_type": inc_type,
        "time_of_day": "night" if any(w in lower_text for w in ['night', 'dark', '10pm', 'late']) else "evening",
        "severity": sev,
        "confidence": 0.85
    }


# FEATURE 3 — SOS Generator
def generate_sos_message(name, location, destination, city):
    prompt = f'''
Write urgent SOS SMS under 160 characters.
Person: {name} in {city}. Last location: {location}.
Going to: {destination}. Ask recipient to call immediately.
'''
    if HAS_GENAI and os.environ.get('GEMINI_API_KEY'):
        try:
            return model.generate_content(prompt).text
        except Exception:
            pass

    return f"EMERGENCY SOS: {name} in {city} near {location}. Heading to {destination}. Please check in and call immediately!"


# FEATURE 4 — City Overview for new cities with no data yet
def get_city_safety_overview(city, country):
    prompt = f'''
Women's safety overview for {city}, {country}.
Include: safer vs concerning area types, time-of-day patterns,
local emergency number for women, one cultural safety tip.
Under 150 words. Label as AI-generated, not real-time.
'''
    if HAS_GENAI and os.environ.get('GEMINI_API_KEY'):
        try:
            return model.generate_content(prompt).text
        except Exception:
            pass

    return (
        f"Women's Safety Overview — {city}, {country}:\n"
        f"• Safer Areas: Main commercial centers and metro station precincts.\n"
        f"• Concerning Areas: Dimly lit side streets and unpopulated alleyways.\n"
        f"• Time Patterns: Increased caution recommended after 10:00 PM.\n"
        f"• Emergency Number: Call 112 for police assistance.\n"
        f"• Cultural Tip: Use designated transit compartments and stay in busy pedestrian corridors.\n"
        f"(AI-generated overview)"
    )
