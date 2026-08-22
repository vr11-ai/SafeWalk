"""
SafeWalk Flask API Server
Bridges the existing Python backend to the new HTML/CSS/JS frontend via REST endpoints.
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for d in [BASE_DIR, os.path.join(BASE_DIR, "backend"), os.path.join(BASE_DIR, "ai_backend")]:
    if d not in sys.path:
        sys.path.insert(0, d)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from safewalk_service import (
    initialize_safewalk_system,
    plan_safe_route,
    process_and_save_user_report,
    ingest_city_news_reports,
    handle_vote,
    ask_safewalk_ai,
)
from report_manager import get_city_stats, get_recent_reports_in_city
from geocoder import geocode_address, get_city_country_from_coords, get_city_landmark_suggestions
from genai_layer import generate_sos_message, get_city_safety_overview

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

initialize_safewalk_system()


@app.route("/")
def serve_index():
    return send_from_directory("frontend", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("frontend", path)


@app.route("/api/landmarks", methods=["GET"])
def api_landmarks():
    city = request.args.get("city", "Dehradun")
    landmarks = get_city_landmark_suggestions(city)
    return jsonify({"city": city, "landmarks": landmarks})


@app.route("/api/route", methods=["POST"])
def api_route():
    data = request.get_json(force=True)
    start = data.get("start", "Clock Tower, Dehradun")
    end = data.get("end", "UPES Bidholi, Dehradun")
    hour = int(data.get("hour", 22))
    city = data.get("city", "Dehradun")
    result = plan_safe_route(start, end, hour=hour, fallback_city=city)
    return jsonify(result)


@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json(force=True)
    text = data.get("text", "")
    city = data.get("city", "Dehradun")
    country = data.get("country", "India")
    if not text.strip():
        return jsonify({"success": False, "error": "Report text is empty."}), 400
    result = process_and_save_user_report(text, current_city=city, country=country)
    return jsonify(result)


@app.route("/api/feed", methods=["GET"])
def api_feed():
    city = request.args.get("city", "Dehradun")
    limit = int(request.args.get("limit", 15))
    rows = get_recent_reports_in_city(city, limit=limit)
    feed = []
    for row in rows:
        inc_id, inc_type, sev, ts_str, up, ver, desc, rlat, rlng = row
        feed.append({
            "id": inc_id, "type": inc_type, "severity": sev,
            "timestamp": ts_str, "upvotes": up, "verified": bool(ver),
            "description": desc, "lat": rlat, "lng": rlng,
        })
    return jsonify({"city": city, "feed": feed})


@app.route("/api/vote", methods=["POST"])
def api_vote():
    data = request.get_json(force=True)
    inc_id = int(data.get("id", 0))
    session_id = data.get("session_id", "anon")
    vote_type = data.get("vote", "up")
    result = handle_vote(inc_id, session_id, vote_type)
    return jsonify(result)


@app.route("/api/stats", methods=["GET"])
def api_stats():
    city = request.args.get("city", "Dehradun")
    stats = get_city_stats(city)
    return jsonify({"city": city, "stats": stats})


@app.route("/api/news", methods=["POST"])
def api_news():
    data = request.get_json(force=True)
    city = data.get("city", "Dehradun")
    country = data.get("country", "India")
    result = ingest_city_news_reports(city, country)
    return jsonify(result)


@app.route("/api/ask", methods=["POST"])
def api_ask():
    data = request.get_json(force=True)
    query = data.get("query", "")
    city = data.get("city", "Dehradun")
    country = data.get("country", "India")
    if not query.strip():
        return jsonify({"answer": "Please ask a question.", "retrieved_context": ""}), 400
    result = ask_safewalk_ai(query, city=city, country=country)
    return jsonify(result)


@app.route("/api/sos", methods=["POST"])
def api_sos():
    data = request.get_json(force=True)
    name = data.get("name", "User")
    current = data.get("current_location", "")
    destination = data.get("destination", "")
    city = data.get("city", "Dehradun")
    msg = generate_sos_message(name, current, destination, city)
    return jsonify({"message": msg})


@app.route("/api/overview", methods=["GET"])
def api_overview():
    city = request.args.get("city", "Dehradun")
    overview = get_city_safety_overview(city)
    return jsonify({"city": city, "overview": overview})


if __name__ == "__main__":
    print("\n  SafeWalk API Server starting on http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
