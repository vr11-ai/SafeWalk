'''
SafeWalk Interactive Terminal CLI Demo
Allows user to test all SafeWalk features interactively in terminal.
'''

import sys
import os

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
from report_manager import get_city_stats, get_recent_reports_in_city


def main():
    initialize_safewalk_system()
    session_id = "cli_user_session_1"
    current_city = "Delhi"

    while True:
        print("\n" + "=" * 55)
        print("   🛡️  SAFEWALK INTERACTIVE USER TERMINAL DEMO")
        print("=" * 55)
        print(f"Current Selected City: {current_city}")
        print("1. 🗺️  Plan Safe Walking Route (Start -> Destination)")
        print("2. 📢  Report Safety Incident in Plain Text (Gemini NLP)")
        print("3. 🔥  View Recent Reports & Upvote Incidents")
        print("4. 🧠  Ask SafeWalk AI Assistant (RAG WHO/NCRB Knowledge)")
        print("5. 🌐  Change Selected City")
        print("6. ❌  Exit Demo")
        print("=" * 55)

        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            start_loc = input("\nEnter Start Location (e.g. Connaught Place, Delhi): ").strip()
            dest_loc = input("Enter Destination (e.g. Lajpat Nagar, Delhi): ").strip()
            hour_str = input("Enter travel hour 0-23 [Default 22 for night]: ").strip()
            hour = int(hour_str) if hour_str.isdigit() else 22

            if not start_loc or not dest_loc:
                print("❌ Start and Destination cannot be empty.")
                continue

            print("\n🔄 Geocoding locations & calculating OSRM routes + AI Briefing...")
            res = plan_safe_route(start_loc, dest_loc, hour=hour)

            if not res.get("success"):
                print(f"❌ Route Planning Error: {res.get('error')}")
            else:
                safest = res["routes"]["safest"]
                fastest = res["routes"]["fastest"]
                print(f"\n✅ City Identified: {res['city']}, {res['country']}")
                print(f"📍 Start Coords: ({res['start']['lat']}, {res['start']['lng']})")
                print(f"📍 Destination Coords: ({res['destination']['lat']}, {res['destination']['lng']})")
                print("\n" + "-" * 50)
                print(f"🟢 SAFEST ROUTE:")
                print(f"   • Safety Score: {safest['safety_avg']}/100")
                print(f"   • Walk Time:    {safest['duration_min']} mins ({safest['distance_m']} meters)")
                print(f"   • Danger Zones: {len(safest['danger_zones'])} detected")

                print(f"\n🔴 FASTEST ROUTE:")
                print(f"   • Safety Score: {fastest['safety_avg']}/100")
                print(f"   • Walk Time:    {fastest['duration_min']} mins ({fastest['distance_m']} meters)")
                print("-" * 50)

                print("\n🤖 AI ROUTE SAFETY BRIEFING (Gemini + RAG Context):")
                print(res["ai_safety_briefing"])

        elif choice == "2":
            user_text = input("\nDescribe what happened (e.g., Catcalling near HKV parking lot at 10pm): ").strip()
            if not user_text:
                print("❌ Report description cannot be empty.")
                continue

            print("\n🔄 Processing report with Gemini NLP & updating real-time safety scores...")
            rep_res = process_and_save_user_report(user_text, current_city=current_city)

            print("\n✅ REPORT SUBMITTED SUCCESSFULLY!")
            print("📑 Extracted NLP Data:", rep_res["nlp_parsed"])
            print("📍 Saved Geocoded Location:", rep_res["saved_location"])
            print("📊 Updated City Statistics:", rep_res["city_stats"])

        elif choice == "3":
            print(f"\n🔥 RECENT REPORTS IN {current_city.upper()}:")
            reports = get_recent_reports_in_city(current_city, limit=8)
            if not reports:
                print(f"No reports found in {current_city}.")
            else:
                for idx, r in enumerate(reports, 1):
                    inc_id, inc_type, sev, ts, up, ver, desc, lat, lng = r
                    v_str = " [✔ VERIFIED]" if ver else ""
                    print(f"\n[{idx}] ID {inc_id} | Type: {inc_type.upper()} | Severity: {sev}/3{v_str}")
                    print(f"    Description: {desc}")
                    print(f"    Time: {ts} | Upvotes: {up} | Coords: ({lat}, {lng})")

                up_choice = input("\nEnter Incident ID to Upvote (or press Enter to skip): ").strip()
                if up_choice.isdigit():
                    inc_id_num = int(up_choice)
                    v_res = handle_vote(inc_id_num, session_id=session_id, vote_type="up")
                    if v_res["success"]:
                        print(f"✅ Upvoted Incident #{inc_id_num} successfully! Weight updated.")
                    else:
                        print("⚠️ Could not upvote (already voted in this session).")

        elif choice == "4":
            query = input("\nAsk a women's safety question (e.g., Is it safe near metro stations at night?): ").strip()
            if not query:
                print("❌ Query cannot be empty.")
                continue

            print("\n🔄 Searching WHO/NCRB Knowledge Base & Gemini AI...")
            ai_res = ask_safewalk_ai(query, city=current_city)
            print("\n💡 AI ANSWER (Grounded in WHO/NCRB Guidelines):")
            print(ai_res["answer"])

        elif choice == "5":
            new_city = input("\nEnter city name (e.g. Delhi, Tokyo, London, Lagos): ").strip()
            if new_city:
                current_city = new_city
                print(f"✅ Switched active city to: {current_city}")

        elif choice == "6":
            print("\n👋 Exiting SafeWalk Demo. Stay Safe!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-6.")


if __name__ == "__main__":
    main()
