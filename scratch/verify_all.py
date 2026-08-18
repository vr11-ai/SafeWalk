import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'frontend'))
sys.path.append(os.path.join(BASE_DIR, 'backend'))
sys.path.append(os.path.join(BASE_DIR, 'ai_backend'))

# Test DB Initialization
from setup_db import init_database, save_incident
init_database()

# Test saving an incident
save_incident(28.6139, 77.2090, 'harassment', 2, 'night', 'Delhi', 'India', 'Test incident near metro')

# Test report manager
from report_manager import update_all_weights, get_recent_reports_in_city, get_city_stats, calculate_weight
update_all_weights()
reports = get_recent_reports_in_city('Delhi')
stats = get_city_stats('Delhi')
weight = calculate_weight(hours_ago=2, upvotes=1, downvotes=0)

# Test safety scorer and router
from router import get_alternative_routes
routes = get_alternative_routes(28.6139, 77.2090, 28.6300, 77.2200, 22)

# Test Gen AI functions
from genai_layer import generate_safety_briefing, process_incident_report, generate_sos_message, get_city_safety_overview
brief = generate_safety_briefing(routes[0], '10:00 PM', 'Delhi', 'India', verified_reports=1, recent_reports=1)
inc_nlp = process_incident_report('I felt unsafe near Connaught Place', 'Delhi', 'India')
sos_msg = generate_sos_message('Priya', 'Connaught Place', 'Mandi House', 'Delhi')
city_ov = get_city_safety_overview('Delhi', 'India')

# Test map builder
from map_builder import build_safety_map, add_routes_to_map
m = build_safety_map(center=[28.6139, 77.2090])
m = add_routes_to_map(m, routes[0], routes[1])

print("ALL COMPONENTS VERIFIED SUCCESSFULLY!")
print(f"- Incident Count: {len(reports)}")
print(f"- City Stats: {stats}")
print(f"- Calculated Weight (2h ago): {weight}")
print(f"- Route 1 Safety Score: {routes[0]['safety_avg']}/100")
print(f"- Incident NLP severity: {inc_nlp['severity']}")
