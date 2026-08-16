import sys
import os
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
AI_BACKEND_DIR = os.path.join(BASE_DIR, "ai_backend")

for d in [BASE_DIR, BACKEND_DIR, AI_BACKEND_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

from safewalk_service import (
    initialize_safewalk_system,
    plan_safe_route,
    process_and_save_user_report,
    handle_vote,
    ask_safewalk_ai,
)


def test_full_integration_pipeline():
    print("==================================================")
    print("  TESTING END-TO-END BACKEND & AI INTEGRATION     ")
    print("==================================================")

    # 1. Initialize system
    print("\n--- 1. Initializing System & DB ---")
    initialize_safewalk_system()

    # 2. Plan Route
    print("\n--- 2. Testing Route Planning & AI Briefing Pipeline ---")
    start_addr = "Connaught Place, Delhi"
    end_addr = "Lajpat Nagar, Delhi"
    res = plan_safe_route(start_addr, end_addr, hour=22)

    assert res["success"] is True, f"Route planning failed: {res.get('error')}"
    print(f"City: {res['city']}, Country: {res['country']}")
    print(f"Start Coords: ({res['start']['lat']}, {res['start']['lng']})")
    print(f"Destination Coords: ({res['destination']['lat']}, {res['destination']['lng']})")
    print(f"Safest Route Score: {res['routes']['safest']['safety_avg']}/100")
    print(f"Fastest Route Duration: {res['routes']['fastest']['duration_min']} mins")
    print("\n[AI Briefing Sample]:")
    print(res["ai_safety_briefing"])

    # 3. Report Incident via NLP
    print("\n--- 3. Testing Natural Language Incident Reporting Pipeline ---")
    report_text = "Felt very unsafe and stalked near Haus Khas metro station entrance at 10:30pm"
    rep_res = process_and_save_user_report(report_text, current_city="Delhi", country="India")

    assert rep_res["success"] is True, "Incident reporting failed"
    print(f"Extracted NLP Data: {rep_res['nlp_parsed']}")
    print(f"Saved Geocoded Coords: ({rep_res['saved_location']['lat']}, {rep_res['saved_location']['lng']})")
    print(f"Updated City Stats: {rep_res['city_stats']}")

    # 4. Community Vote with Unique Session ID
    print("\n--- 4. Testing Community Voting Pipeline ---")
    unique_session = f"session_{uuid.uuid4().hex[:8]}"
    vote_res = handle_vote(incident_id=1, session_id=unique_session, vote_type="up")
    print(f"Upvote Result for {unique_session}: {vote_res}")
    assert vote_res["success"] is True, "Voting failed"

    # 5. RAG AI Assistant
    print("\n--- 5. Testing RAG Knowledge Assistant Query ---")
    rag_res = ask_safewalk_ai("Is it safe to walk near metro stations late at night?", city="Delhi")
    print("\n[RAG Answer]:")
    print(rag_res["answer"])

    print("\n==================================================")
    print("  ALL INTEGRATION TESTS PASSED SUCCESSFULLY!       ")
    print("==================================================")


if __name__ == "__main__":
    test_full_integration_pipeline()
