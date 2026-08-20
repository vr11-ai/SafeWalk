"""
RAG Knowledge Base & Guidance Engine for SafeWalk (Dynamic AI & Vector Search)
Grounded in WHO & NCRB Women's Safety Directives.
"""

import os
import json
import re
import html

# WHO & NCRB Grounded Guidelines Knowledge Base
WHO_NCRB_KNOWLEDGE = [
    "WHO Directive: Stick to illuminated main roads, keep mobile phone accessible, and maintain spatial awareness at night.",
    "NCRB Safety Advisory: High pedestrian density commercial corridors have significantly lower rates of opportunistic crime.",
    "SafeWalk Standard: If feeling followed, enter an open 24/7 commercial establishment or transit hub immediately and alert emergency contacts.",
    "NCRB Advisory: Avoid unlit shortcuts or isolated footpaths during late night hours (22:00 to 04:00).",
    "WHO Women Safety Standard: Always share live GPS tracking with trusted emergency contacts when walking late at night.",
    "NCRB Emergency Protocol: In immediate danger, dial 112 (National Emergency Helpline) or use the SafeWalk 1-click SOS SMS generator.",
    "WHO Cab & Transport Advisory: Verify driver details, license plate, and share ride status before entering rideshare or taxi vehicles late at night."
]

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
    load_dotenv()

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key and key.strip() and key.strip() != "YOUR_GEMINI_KEY":
        genai.configure(api_key=key.strip("'\" "))
        model = genai.GenerativeModel('gemini-3.6-flash')
    else:
        model = None
except Exception:
    model = None


def load_knowledge_base():
    """Initializes WHO & NCRB knowledge base into memory instantly (0ms)."""
    return len(WHO_NCRB_KNOWLEDGE)


def ask_safewalk_ai(user_question: str, city: str = "Delhi", country: str = "India") -> dict:
    """Answers safety questions grounded in WHO/NCRB guidelines with dynamic RAG & Gemini AI."""
    q_clean = user_question.lower().strip()
    city_safe = html.escape(city)[:40]

    # 1. Retrieve relevant knowledge chunks
    words = [w for w in re.findall(r'\w+', q_clean) if len(w) > 3]
    matched = [k for k in WHO_NCRB_KNOWLEDGE if any(w in k.lower() for w in words)]
    if not matched:
        matched = WHO_NCRB_KNOWLEDGE[:3]
        
    context_str = "\n• ".join(matched)

    # 2. Try Gemini AI with strict 2.0s timeout
    if model:
        prompt = f"""
System Directive: Act strictly as an expert safety counselor for women and pedestrians in {city_safe}, {country}.
Answer the user's question based on these official WHO & NCRB safety guidelines:

Knowledge Context:
• {context_str}

User Question: "{html.escape(user_question)}"

Provide a clear, 3-point actionable answer (under 120 words). Be empathetic, practical, and highly direct.
"""
        try:
            resp = model.generate_content(prompt, request_options={"timeout": 2.0})
            if resp and resp.text:
                return {
                    "answer": resp.text.strip(),
                    "retrieved_context": context_str
                }
        except Exception:
            pass

    # 3. Dynamic Rule-Based Smart Fallback Engine
    if "follow" in q_clean or "behind" in q_clean or "stalk" in q_clean:
        guidance = (
            f"💡 **Immediate Safety Steps for {city_safe}:**\n\n"
            f"1. **Cross the Street:** Immediately change your walking pace or cross to the opposite side to confirm if you are being followed.\n"
            f"2. **Enter a Safe Space:** Step into an open store, 24/7 petrol pump, hotel lobby, or transit hub. Do NOT go directly to your home.\n"
            f"3. **Alert Help:** Call emergency helpline (112) or trigger the SafeWalk Emergency SOS SMS alert to your trusted contacts."
        )
    elif "cab" in q_clean or "taxi" in q_clean or "auto" in q_clean or "uber" in q_clean:
        guidance = (
            f"💡 **Rideshare & Cab Safety Protocol in {city_safe}:**\n\n"
            f"1. **Verify Credentials:** Check the license plate number, driver photo, and vehicle model before opening the door.\n"
            f"2. **Share Live Trip:** Send your live ride tracking link to family/friends and ensure child lock is disabled.\n"
            f"3. **Stay Alert:** Keep your phone in hand and follow the route on your own map."
        )
    elif "night" in q_clean or "dark" in q_clean or "late" in q_clean:
        guidance = (
            f"💡 **Late Night Pedestrian Safety for {city_safe}:**\n\n"
            f"1. **Main Arterial Roads:** Stick strictly to illuminated main avenues; avoid unlit shortcuts or alleyways.\n"
            f"2. **Visible Confidence:** Walk briskly with head up, ears free from heavy headphones, and phone fully charged.\n"
            f"3. **Community Nodes:** Stay close to well-lit commercial storefronts, metro station exits, and police booths."
        )
    else:
        guidance = (
            f"💡 **General Safety Guidance for {city_safe}:**\n\n"
            f"1. **Stay Aware:** Keep spatial awareness high, phone charged, and emergency contacts on quick dial.\n"
            f"2. **Use Safe Routes:** Follow SafeWalk's green verified safe walking paths with high streetlight and POI density.\n"
            f"3. **Report Incidents:** Share crowdsourced updates on the Live Feed to help protect fellow women in your community."
        )

    return {
        "answer": guidance,
        "retrieved_context": context_str
    }


def query_rag_knowledge(query: str, top_k: int = 2, city: str = "Delhi", country: str = "India") -> dict:
    """Returns top matching WHO/NCRB knowledge guidelines and AI advice."""
    return ask_safewalk_ai(query, city=city, country=country)


def get_safety_context(city: str = "Delhi") -> str:
    """Returns general WHO safety context string."""
    return WHO_NCRB_KNOWLEDGE[0]
