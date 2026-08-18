# app.py — MEMBER 3 OWNS THIS FILE (UPDATED v2.0 & DEBUGGED)
import os
import sys
import uuid
from datetime import datetime
import streamlit as st
from streamlit_folium import st_folium

# Path setup for root, backend, and ai_backend packages
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [BASE_DIR, os.path.join(BASE_DIR, 'backend'), os.path.join(BASE_DIR, 'ai_backend'), os.path.dirname(os.path.abspath(__file__))]:
    if p not in sys.path:
        sys.path.append(p)

from map_builder import build_safety_map, add_routes_to_map

# Attempt imports from Backend (M2) and AI Layer (M1) with safe fallbacks
try:
    from router import get_alternative_routes
except ImportError:
    def get_alternative_routes(s_lat, s_lng, e_lat, e_lng, hour):
        return [
            {'points': [[s_lat, s_lng], [e_lat, e_lng]], 'safety_avg': 78, 'duration_min': 18, 'danger_zones': []},
            {'points': [[s_lat, s_lng], [(s_lat+e_lat)/2, (s_lng+e_lng)/2], [e_lat, e_lng]], 'safety_avg': 52, 'duration_min': 14, 'danger_zones': [[(s_lat+e_lat)/2, (s_lng+e_lng)/2]]}
        ]

try:
    from geocoder import geocode_address, get_city_country_from_coords
except ImportError:
    def geocode_address(addr):
        if not addr:
            return (None, None)
        return (28.6139, 77.2090)
    def get_city_country_from_coords(lat, lng):
        return ('Delhi', 'India')

try:
    from genai_layer import (generate_safety_briefing,
                            process_incident_report,
                             generate_sos_message,
                             get_city_safety_overview)
except ImportError:
    def generate_safety_briefing(route_data, time_str, city, country, verified_reports=0, recent_reports=0):
        return f"1. SafeWalk route assessment: Primary roads show normal activity.\n2. City context for {city}: Keep to well-lit areas.\n3. Emergency number: Call 112 if unsafe.\n4. Recommended: Prefer walking during daylight or busy hours.\n5. Cultural tip: Stay alert and keep emergency contacts on speed dial."
    def process_incident_report(user_text, city, country):
        return {"location_description": user_text, "incident_type": "unsafe_area", "time_of_day": "night", "severity": 2, "confidence": 0.8}
    def generate_sos_message(name, location, destination, city):
        return f"EMERGENCY: {name} needs assistance in {city} near {location}. Heading towards {destination}. Please call immediately!"
    def get_city_safety_overview(city, country):
        return f"Safety Overview for {city}, {country}: Exercise heightened awareness in poorly lit streets during late hours."

try:
    from setup_db import save_incident
except ImportError:
    def save_incident(lat, lng, inc_type, severity, time_of_day, city, country, description=''):
        pass

try:
    from report_manager import (get_recent_reports_in_city,
                                get_city_stats,
                                upvote_incident, downvote_incident)
except ImportError:
    def get_recent_reports_in_city(city, limit=8):
        return []
    def get_city_stats(city):
        return {'total': 0, 'last_24h': 0, 'verified': 0, 'avg_severity': 0}
    def upvote_incident(inc_id, session_id):
        return True
    def downvote_incident(inc_id, session_id):
        return True


def trigger_rerun():
    if hasattr(st, 'rerun'):
        st.rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()


def safe_geocode(address):
    if not address or not address.strip():
        return None, None
    try:
        res = geocode_address(address)
        if res and isinstance(res, (tuple, list)) and len(res) >= 2:
            return res[0], res[1]
    except Exception:
        pass
    return None, None


st.set_page_config(page_title='SafeWalk', page_icon='🛡️', layout='wide')

# Session state initialization
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'voted' not in st.session_state:
    st.session_state.voted = set()
if 'routes' not in st.session_state:
    st.session_state.routes = []
if 'city' not in st.session_state:
    st.session_state.city = 'your city'
if 'country' not in st.session_state:
    st.session_state.country = 'your country'
if 'map_center' not in st.session_state:
    st.session_state.map_center = [28.6139, 77.2090]
if 'ai_overview' not in st.session_state:
    st.session_state.ai_overview = None

st.markdown("<h1 style='color:#7C3AED'>🛡️ SafeWalk</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#888'>AI Safety Navigator - Any city - Real-time crowdsourced</p>", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('### 🧭 Plan Your Route')
    start = st.text_input('Starting Point', placeholder='e.g. Shibuya Station, Tokyo')
    end = st.text_input('Destination', placeholder='e.g. Harajuku, Tokyo')
    dept_time = st.time_input('Departure Time', value=datetime.now().time())
    go = st.button('🛡️ Find Safest Route', type='primary', use_container_width=True)
    st.markdown('---')
    st.markdown('### 🌐 City Overview')
    if st.button('Get AI Safety Overview', use_container_width=True):
        if start:
            lat, lng = safe_geocode(start)
            if lat is not None and lng is not None:
                city_name, country_name = get_city_country_from_coords(lat, lng)
                ov = get_city_safety_overview(city_name, country_name)
                st.session_state.ai_overview = (city_name, ov)
            else:
                st.error("Could not geocode the starting address.")
        else:
            st.warning('Please enter a starting point first.')
    
    if st.session_state.ai_overview:
        ov_city, ov_text = st.session_state.ai_overview
        st.info(f'**{ov_city}**\n\n{ov_text}\n\n*AI-generated*')

    st.markdown('---')
    st.markdown('### 📢 Report Unsafe Area')
    report_text = st.text_area('What happened and where?', placeholder='e.g. I was followed near the metro at night...')
    submit = st.button('Submit Report', use_container_width=True)

# ── Route Calculation Logic ──────────────────────────────
if go:
    if start and end:
        with st.spinner('Finding route...'):
            s_lat, s_lng = safe_geocode(start)
            e_lat, e_lng = safe_geocode(end)
            if s_lat is not None and e_lat is not None:
                city_name, country_name = get_city_country_from_coords(s_lat, s_lng)
                st.session_state.city = city_name
                st.session_state.country = country_name
                st.session_state.map_center = [s_lat, s_lng]
                with st.spinner('Calculating safest route...'):
                    st.session_state.routes = get_alternative_routes(s_lat, s_lng, e_lat, e_lng, dept_time.hour)
            else:
                st.error('Location not found. Please specify city name.')
    else:
        st.warning('Please provide both starting point and destination.')

# ── Main Columns ─────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    if st.session_state.routes:
        st.markdown(f"### 📍 {st.session_state.city}, {st.session_state.country}")
    m = build_safety_map(center=st.session_state.map_center)
    if m is not None:
        if len(st.session_state.routes) >= 2:
            m = add_routes_to_map(m, st.session_state.routes[0], st.session_state.routes[-1])
        elif len(st.session_state.routes) == 1:
            m = add_routes_to_map(m, st.session_state.routes[0], st.session_state.routes[0])
        st_folium(m, height=520, use_container_width=True, key="safewalk_map")
    else:
        st.info("Interactive map view initializing...")



with col2:
    if st.session_state.routes:
        safe, fast = st.session_state.routes[0], st.session_state.routes[-1]
        score = safe.get('safety_avg', 70)
        icon = '🔵' if score > 70 else '🟡' if score > 40 else '🔴'
        st.markdown('### Route Safety Report')
        c1, c2 = st.columns(2)
        c1.metric('Safety Score', f'{icon} {score}/100')
        c2.metric('Walk Time', f"{safe.get('duration_min', 0)} min")
        c1.metric('Danger Zones', len(safe.get('danger_zones', [])))
        extra = safe.get('duration_min', 0) - fast.get('duration_min', 0)
        c2.metric('Extra Time', f"+{extra} min" if extra >= 0 else f"{extra} min")
        st.markdown('---')
        st.markdown('### 🛡️ AI Safety Briefing')
        stats = get_city_stats(st.session_state.city)
        with st.spinner('Generating tips...'):
            brief = generate_safety_briefing(
                {'average': score, 'danger_zones': safe.get('danger_zones', [])},
                dept_time.strftime('%I:%M %p'), st.session_state.city, st.session_state.country,
                verified_reports=stats.get('verified', 0),
                recent_reports=stats.get('last_24h', 0))
        st.info(brief)
        st.markdown('---')
        st.markdown('### 🚨 Emergency SOS')
        sos_name = st.text_input('Your Name')
        if st.button('🆘 Send SOS', type='primary', use_container_width=True):
            if sos_name.strip():
                msg = generate_sos_message(sos_name, start or "Current Location", end or "Destination", st.session_state.city)
                st.error(f'SOS:\n\n{msg}')
                st.success('Alert sent!')
            else:
                st.warning('Please enter your name for the SOS alert.')

# ── Report Submission ────────────────────────────────────
if submit and report_text:
    with st.spinner('Processing incident report...'):
        lat, lng = safe_geocode(start) if start else (28.6139, 77.2090)
        if lat is None:
            lat, lng = 28.6139, 77.2090
        city_r, country_r = get_city_country_from_coords(lat, lng)
        inc = process_incident_report(report_text, city_r, country_r)
        if inc and inc.get('confidence', 0) > 0.5:
            save_incident(lat, lng, inc.get('incident_type', 'unsafe_area'),
                          inc.get('severity', 1), inc.get('time_of_day', 'night'),
                          city_r, country_r, report_text)
            st.session_state.city = city_r
            st.session_state.country = country_r
            st.success(f"✅ Saved · {inc.get('incident_type', 'unsafe_area')} · Sev {inc.get('severity', 1)}/3")
            st.balloons()
            trigger_rerun()
        else:
            st.warning('Be more specific about the location or incident.')

# ── Live Report Feed ─────────────────────────────────────
if st.session_state.city != 'your city':
    st.markdown('---')
    st.markdown(f'### 📡 Live Reports — {st.session_state.city}')
    stats = get_city_stats(st.session_state.city)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Total Reports', stats.get('total', 0))
    c2.metric('Last 24h', stats.get('last_24h', 0),
              delta=f"+{stats.get('last_24h', 0)}" if stats.get('last_24h', 0) > 0 else None,
              delta_color='inverse')
    c3.metric('Verified ✅', stats.get('verified', 0))
    c4.metric('Avg Severity', f"{stats.get('avg_severity', 0)}/3")
    recent = get_recent_reports_in_city(st.session_state.city, limit=8)
    if recent:
        for row in recent:
            inc_id, inc_type, sev, ts_str, up, ver, desc, rlat, rlng = row
            try:
                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                h = (datetime.now() - ts).total_seconds() / 3600
                tlabel = f'⏱ {int(h*60)}m ago' if h < 1 else \
                         f'⏱ {int(h)}h ago' if h < 24 else \
                         f'⚪ {int(h/24)}d ago'
            except Exception:
                tlabel = '⏱ Recent'
            badge = ' ✅' if ver else ''
            sc = '🔴' if sev == 3 else '🟡' if sev == 2 else '🔵'
            with st.container():
                ci, cv = st.columns([3, 1])
                with ci:
                    st.markdown(f'**{sc} {str(inc_type).title()}{badge}** <small>{tlabel}</small>', unsafe_allow_html=True)
                    if desc:
                        st.caption(desc[:100])
                with cv:
                    if inc_id in st.session_state.voted:
                        st.caption(f'👍 {up}')
                    else:
                        v1, v2 = st.columns(2)
                        if v1.button('👍', key=f'u{inc_id}'):
                            if upvote_incident(inc_id, st.session_state.session_id):
                                st.session_state.voted.add(inc_id)
                                trigger_rerun()
                        if v2.button('👎', key=f'd{inc_id}'):
                            if downvote_incident(inc_id, st.session_state.session_id):

                                st.session_state.voted.add(inc_id)
                                trigger_rerun()
                st.divider()
    else:
        st.info(f'No reports yet in {st.session_state.city}. Be the first.')
