# prompts.py — MEMBER 1 OWNS THIS FILE
SAFETY_ADVISOR_PROMPT = """
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
"""

INCIDENT_NLP_PROMPT = """
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
"""

SOS_PROMPT = """
Write urgent SOS SMS under 160 characters.
Person: {name} in {city}. Last location: {location}.
Going to: {destination}. Ask recipient to call immediately.
"""

CITY_OVERVIEW_PROMPT = """
Women's safety overview for {city}, {country}.
Include: safer vs concerning area types, time-of-day patterns,
local emergency number for women, one cultural safety tip.
Under 150 words. Label as AI-generated, not real-time.
"""
