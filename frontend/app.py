# app.py - SafeWalk Streamlit Frontend (Security Hardened against XSS)
import os
import sys
import uuid
import html
from datetime import datetime
import streamlit as st
from streamlit_folium import st_folium

# Path setup for root, backend, and ai_backend packages
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
AI_BACKEND_DIR = os.path.join(BASE_DIR, "ai_backend")

for p in [BASE_DIR, BACKEND_DIR, AI_BACKEND_DIR, os.path.dirname(os.path.abspath(__file__))]:
    if p not in sys.path:
        sys.path.insert(0, p)

from map_builder import build_safety_map, add_routes_to_map

# Imports from unified safewalk_service API
from safewalk_service import (
    initialize_safewalk_system,
    plan_safe_route,
    process_and_save_user_report,
    ingest_city_news_reports,
    handle_vote,
    ask_safewalk_ai,
)
from report_manager import get_city_stats, get_recent_reports_in_city, upvote_incident, downvote_incident
from geocoder import geocode_address, get_city_country_from_coords, get_city_landmark_suggestions
from genai_layer import generate_safety_briefing, generate_sos_message, process_incident_report, get_city_safety_overview

# Page Configuration
st.set_page_config(
    page_title="SafeWalk | AI Women's Safety Navigation",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #8892b0;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #2d3748;
        text-align: center;
    }
    .verified-badge {
        background-color: #10B981;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB & Session State
initialize_safewalk_system()

if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"
if "voted" not in st.session_state:
    st.session_state.voted = set()
if "city" not in st.session_state:
    st.session_state.city = "Dehradun"
if "country" not in st.session_state:
    st.session_state.country = "India"
if "routes" not in st.session_state:
    st.session_state.routes = []
if "map_center" not in st.session_state:
    st.session_state.map_center = [30.3243, 78.0419]
if "ai_overview" not in st.session_state:
    st.session_state.ai_overview = None
if "current_briefing" not in st.session_state:
    st.session_state.current_briefing = None

# Sidebar Controls
with st.sidebar:
    st.markdown("## 🛡️ SafeWalk v2.0")
    st.caption("AI-Powered Real-Time Safety Navigation")
    
    st.markdown("### 🌐 Select Active City")
    
    with st.form("city_selector_form"):
        city_options = [
            "Dehradun", "Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai", "Hyderabad",
            "Tokyo", "London", "Paris", "New York", "Lagos", "Dubai", "Singapore"
        ]
        
        sel_city = st.selectbox("Popular Cities:", city_options, index=0, key="sb_city_select")
        cust_city = st.text_input("Or Type Custom City Name:", placeholder="e.g. Sydney, Berlin", key="sb_custom_city_input")
        city_submit = st.form_submit_button("Set Active City 📍", use_container_width=True)
        
        if city_submit:
            target_city = cust_city.strip().title() if cust_city.strip() else sel_city
            lat_c, lng_c = geocode_address(target_city)
            if lat_c is not None:
                st.session_state.city = html.escape(target_city)[:40]
                st.session_state.map_center = [lat_c, lng_c]
                city_g, country_g = get_city_country_from_coords(lat_c, lng_c)
                st.session_state.country = html.escape(country_g if country_g != "Unknown Country" else "Worldwide")[:40]
                st.session_state.routes = []
                st.session_state.current_briefing = None
                st.success(f"Active city set to **{st.session_state.city}**!")
            else:
                st.error(f"Could not locate '{target_city}'. Please check spelling.")
            
    st.info(f"📍 Current Active City: **{st.session_state.city}** ({st.session_state.country})")
    
    travel_hour = st.slider("Time of Travel (Hour):", 0, 23, 22, key="sb_travel_hour")
    time_label = f"{travel_hour:02d}:00 ({'Night' if travel_hour >= 20 or travel_hour < 6 else 'Day'})"
    st.caption(f"🕒 Travel Time: **{time_label}**")
    
    st.divider()
    st.markdown("### 🤖 AI Actions")
    if st.button(f"📰 Fetch AI News for {st.session_state.city}", use_container_width=True, key="sb_news_btn"):
        with st.spinner(f"Ingesting live news & crime reports for {st.session_state.city}..."):
            n_res = ingest_city_news_reports(st.session_state.city, st.session_state.country)
            st.success(f"Ingested {n_res['ingested_count']} news alerts for {st.session_state.city}!")
            st.rerun()

    if st.button("🌐 City Safety Overview", use_container_width=True, key="sb_overview_btn"):
        with st.spinner(f"Analyzing safety patterns for {st.session_state.city}..."):
            ov = get_city_safety_overview(st.session_state.city)
            st.session_state.ai_overview = (st.session_state.city, ov)

    if st.session_state.ai_overview:
        ov_c, ov_t = st.session_state.ai_overview
        st.info(f"**Overview for {html.escape(ov_c)}:**\n\n{html.escape(ov_t)}")
        
    st.divider()
    st.caption(f"Session ID: `{st.session_state.session_id}`")

# Header Section
st.markdown('<div class="main-title">🛡️ SafeWalk — AI Women&#39;s Safety Navigation</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-title">Real-time crowdsourced safety routes & Gemini AI guidance for <b>{html.escape(st.session_state.city)}, {html.escape(st.session_state.country)}</b></div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Plan Safe Route", 
    "📢 Report Incident (NLP)", 
    "🔥 Live Community Feed", 
    "🧠 Ask SafeWalk AI & SOS"
])

# -----------------------------------------------------------------------------
# TAB 1: ROUTE PLANNING
# -----------------------------------------------------------------------------
with tab1:
    landmarks = get_city_landmark_suggestions(st.session_state.city)
    
    # Auto-update widget state when city changes or defaults are unset
    default_start = landmarks[0] if len(landmarks) > 0 else f"Clock Tower, {st.session_state.city}"
    default_dest = landmarks[1] if len(landmarks) > 1 else f"UPES Bidholi, {st.session_state.city}"

    if "direct_start_text_input" not in st.session_state or st.session_state.get("active_city_tracker") != st.session_state.city:
        st.session_state["direct_start_text_input"] = default_start
    if "direct_dest_text_input" not in st.session_state or st.session_state.get("active_city_tracker") != st.session_state.city:
        st.session_state["direct_dest_text_input"] = default_dest
    st.session_state["active_city_tracker"] = st.session_state.city

    st.markdown(f"#### 📍 Quick Destination Suggestions for **{st.session_state.city}**:")
    sug_cols = st.columns(min(len(landmarks), 5))
    for idx, lm in enumerate(landmarks[:5]):
        with sug_cols[idx]:
            chip_label = f"📌 {lm.split(',')[0]}"
            if st.button(chip_label, key=f"lm_chip_{idx}"):
                st.session_state["direct_dest_text_input"] = lm
                st.rerun()

    with st.form("route_planning_form"):
        col_in1, col_in2, col_go = st.columns([4, 4, 3])
        
        with col_in1:
            start_input = st.text_input(
                f"Start Location in {st.session_state.city}:",
                placeholder=f"Type ANY location in {st.session_state.city}...",
                key="direct_start_text_input"
            )
                
        with col_in2:
            end_input = st.text_input(
                f"Destination in {st.session_state.city}:",
                placeholder=f"Type ANY location in {st.session_state.city}...",
                key="direct_dest_text_input"
            )
                
        with col_go:
            st.write("")
            st.write("")
            go_btn = st.form_submit_button("🚀 Find Safest Route", use_container_width=True, type="primary")

    if go_btn:
        s_loc = start_input.strip() if start_input.strip() else f"Clock Tower, {st.session_state.city}"
        e_loc = end_input.strip() if end_input.strip() else f"UPES Bidholi, {st.session_state.city}"
        
        st.session_state.s_input_val = s_loc
        st.session_state.d_input_val = e_loc
        
        with st.spinner(f"Geocoding & calculating safest walking route in {st.session_state.city}..."):
            r_res = plan_safe_route(s_loc, e_loc, hour=travel_hour, fallback_city=st.session_state.city)
            if r_res["success"]:
                if r_res["city"] and r_res["city"] != "Unknown City":
                    st.session_state.city = r_res["city"]
                st.session_state.country = r_res["country"]
                st.session_state.routes = [r_res["routes"]["safest"], r_res["routes"]["fastest"]]
                st.session_state.map_center = [r_res["start"]["lat"], r_res["start"]["lng"]]
                st.session_state.current_briefing = r_res["ai_safety_briefing"]
            else:
                st.error(r_res.get("error", "Route planning failed."))

    col_map, col_report = st.columns([7, 5])
    
    with col_map:
        st.markdown(f"### 📍 Interactive Map: {html.escape(st.session_state.city)}, {html.escape(st.session_state.country)}")
        m = build_safety_map(center=st.session_state.map_center)
        if m is not None:
            if len(st.session_state.routes) >= 2:
                m = add_routes_to_map(m, st.session_state.routes[0], st.session_state.routes[1])
            elif len(st.session_state.routes) == 1:
                m = add_routes_to_map(m, st.session_state.routes[0], st.session_state.routes[0])
            st_folium(m, height=480, use_container_width=True, key="safewalk_map_view")
            
    with col_report:
        if st.session_state.routes:
            safe, fast = st.session_state.routes[0], st.session_state.routes[-1]
            score = safe.get('safety_avg', 70)
            icon = '🟢' if score >= 70 else '🟡' if score >= 45 else '🔴'
            
            st.markdown("### 📊 Route Metrics")
            m1, m2 = st.columns(2)
            m1.metric("Safety Score", f"{icon} {score}/100")
            m2.metric("Walk Time", f"{safe.get('duration_min', 0)} mins")
            
            m3, m4 = st.columns(2)
            m3.metric("Danger Zones", len(safe.get('danger_zones', [])))
            extra = safe.get('duration_min', 0) - fast.get('duration_min', 0)
            m4.metric("Extra Time", f"+{extra} mins" if extra >= 0 else f"{extra} mins")
            
            st.divider()
            st.markdown("### 🤖 AI Route Safety Briefing")
            brief = st.session_state.get("current_briefing")
            if not brief:
                stats = get_city_stats(st.session_state.city)
                brief = generate_safety_briefing(
                    score, f"{travel_hour:02d}:00", st.session_state.city, st.session_state.country,
                    verified_reports=stats.get("verified", 0), recent_reports=stats.get("last_24h", 0)
                )
            st.info(brief)
        else:
            st.info(f"Select locations above and click **Find Safest Route** to calculate walking routes in **{st.session_state.city}**.")

# -----------------------------------------------------------------------------
# TAB 2: INCIDENT REPORTING (NLP)
# -----------------------------------------------------------------------------
with tab2:
    st.markdown(f"### 📢 Report an Unsafe Incident in {st.session_state.city}")
    st.caption("No complicated forms. Describe what happened in plain English or Hindi. Gemini NLP extracts location, incident type, and severity automatically.")
    
    with st.form("nlp_report_form"):
        rep_text = st.text_area(
            "What happened and where?", 
            placeholder=f"e.g. Catcalling and aggressive shouting near main station in {st.session_state.city} at 10pm...", 
            height=100,
            key="nlp_report_text_area"
        )
        sub_btn = st.form_submit_button("🚨 Submit Incident Report", type="primary")
    
    if sub_btn and rep_text.strip():
        with st.spinner("Processing report with Gemini NLP & updating real-time map weights..."):
            r_out = process_and_save_user_report(rep_text, current_city=st.session_state.city, country=st.session_state.country)
            if r_out["success"]:
                st.balloons()
                st.success(f"Report saved successfully! Geocoded Location: ({r_out['saved_location']['lat']}, {r_out['saved_location']['lng']})")
                st.json(r_out["nlp_parsed"])
                st.rerun()
            else:
                st.error("Could not process report. Please be more specific.")

# -----------------------------------------------------------------------------
# TAB 3: LIVE FEED & VOTING (XSS Protected)
# -----------------------------------------------------------------------------
with tab3:
    st.markdown(f"### 🔥 Live Community Incident Feed for {st.session_state.city}")
    stats = get_city_stats(st.session_state.city)
    
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Reports", stats.get("total", 0))
    s2.metric("Last 24 Hours", stats.get("last_24h", 0))
    s3.metric("Verified Reports ✔", stats.get("verified", 0))
    s4.metric("Avg Severity", f"{stats.get('avg_severity', 0.0)} / 3")
    
    st.divider()
    recent = get_recent_reports_in_city(st.session_state.city, limit=10)
    if recent:
        for row in recent:
            inc_id, inc_type, sev, ts_str, up, ver, desc, rlat, rlng = row
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                h = (datetime.now() - ts).total_seconds() / 3600
                tlabel = f"🕒 {int(h*60)}m ago" if h < 1 else f"🕒 {int(h)}h ago" if h < 24 else f"📅 {int(h/24)}d ago"
            except Exception:
                tlabel = "🕒 Recent"
                
            badge = " <span class='verified-badge'>✔ Verified</span>" if ver else ""
            sc_icon = "🔴" if sev == 3 else "🟠" if sev == 2 else "🟡"
            
            # HTML XSS Sanitization
            safe_desc = html.escape(str(desc)) if desc else ""
            safe_type = html.escape(str(inc_type))
            
            with st.container():
                ci, cv = st.columns([4, 1])
                with ci:
                    st.markdown(f"**{sc_icon} {safe_type.upper()}{badge}** • <small>{tlabel}</small>", unsafe_allow_html=True)
                    if safe_desc:
                        st.write(safe_desc)
                    st.caption(f"Coordinates: ({rlat}, {rlng}) • Upvotes: {up}")
                with cv:
                    if inc_id in st.session_state.voted:
                        st.caption("👍 Voted")
                    else:
                        v1, v2 = st.columns(2)
                        if v1.button("👍", key=f"u_{inc_id}"):
                            if handle_vote(inc_id, st.session_state.session_id, "up")["success"]:
                                st.session_state.voted.add(inc_id)
                                st.rerun()
                        if v2.button("👎", key=f"d_{inc_id}"):
                            if handle_vote(inc_id, st.session_state.session_id, "down")["success"]:
                                st.session_state.voted.add(inc_id)
                                st.rerun()
                st.divider()
    else:
        st.info(f"No active reports yet in {st.session_state.city}. Be the first to report or click **Fetch AI News** in the sidebar!")

# -----------------------------------------------------------------------------
# TAB 4: RAG AI ASSISTANT & SOS
# -----------------------------------------------------------------------------
with tab4:
    col_rag, col_sos = st.columns(2)
    
    with col_rag:
        st.markdown("### 🧠 SafeWalk RAG AI Assistant")
        st.caption(f"Answers grounded in official WHO & NCRB Women's Safety Guidelines for {st.session_state.city}.")
        
        with st.form("rag_assistant_form"):
            user_q = st.text_input(
                "Ask a safety question:", 
                value=f"What should I do if I feel followed by someone at night in {st.session_state.city}?",
                key="rag_safety_question_input"
            )
            rag_ask_btn = st.form_submit_button("🔍 Ask AI Assistant")
            
        if "rag_last_response" not in st.session_state:
            st.session_state.rag_last_response = None
            
        if rag_ask_btn and user_q.strip():
            with st.spinner("Searching WHO/NCRB knowledge base & Gemini AI..."):
                st.session_state.rag_last_response = ask_safewalk_ai(user_q, city=st.session_state.city, country=st.session_state.country)
                
        if st.session_state.rag_last_response:
            rag_out = st.session_state.rag_last_response
            st.markdown("#### 💡 AI Guidance:")
            st.info(rag_out["answer"])
            with st.expander("Show Retrieved Knowledge Base Context"):
                st.text(rag_out.get("retrieved_context", ""))
                    
    with col_sos:
        st.markdown("### 🆘 Emergency SOS Alert Generator")
        with st.form("sos_generator_form"):
            sos_user = st.text_input("Your Name:", value="Aditi", key="sos_user_name_input")
            sos_start = st.text_input("Current Location:", value=f"Main Square, {st.session_state.city}", key="sos_start_loc_input")
            sos_dest = st.text_input("Destination Location:", value=f"Central Area, {st.session_state.city}", key="sos_dest_loc_input")
            sos_gen_btn = st.form_submit_button("📲 Generate Emergency SMS", type="primary")
            
        if sos_gen_btn:
            if sos_user.strip():
                sms_msg = generate_sos_message(sos_user, sos_start, sos_dest, st.session_state.city)
                st.warning(f"**SMS Alert Text (<160 chars):**\n\n{html.escape(sms_msg)}")
            else:
                st.warning("Please enter your name for the emergency alert.")
