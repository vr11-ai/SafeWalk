 # map_builder.py — MEMBER 3 OWNS THIS FILE (UPDATED v2.0)
import os
import sys
import sqlite3
from datetime import datetime

try:
    import folium
    from folium.plugins import HeatMap, MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# Path configuration for modular imports across project folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [BASE_DIR, os.path.join(BASE_DIR, 'backend'), os.path.join(BASE_DIR, 'ai_backend'), os.path.dirname(os.path.abspath(__file__))]:
    if p not in sys.path:
        sys.path.append(p)

try:
    from report_manager import update_all_weights
except ImportError:
    def update_all_weights():
        pass


def build_safety_map(center=[28.6139, 77.2090], zoom=13):
    if not HAS_FOLIUM:
        return None

    try:
        update_all_weights() # refresh weights on every load
    except Exception:
        pass

    m = folium.Map(location=center, zoom_start=zoom, tiles='CartoDB dark_matter')
    
    db_path = os.path.join(BASE_DIR, 'safewalk.db')
    if not os.path.exists(db_path):
        db_path = 'safewalk.db'

    rows = []
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute('''
            SELECT lat,lng,severity,type,timestamp,
                   upvotes,verified,weight,description,id
            FROM incidents WHERE weight>0.05
            ORDER BY weight DESC
        ''').fetchall()
        conn.close()
    except Exception:
        rows = []

    now = datetime.now()
    if rows:
        HeatMap([[r[0], r[1], r[7]] for r in rows],
                gradient={0.2: 'green', 0.5: 'yellow', 0.8: 'orange', 1.0: 'red'},
                radius=25, blur=15, min_opacity=0.3).add_to(m)
        cluster = MarkerCluster().add_to(m)
        for lat, lng, sev, inc_type, ts_str, up, ver, wt, desc, inc_id in rows:
            color = 'red' if sev == 3 else 'orange' if sev == 2 else 'yellow'
            wt_val = float(wt) if wt is not None else 1.0
            radius = max(6, min(16, int(wt_val * 12))) # size by recency
            try:
                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                h = (now - ts).total_seconds() / 3600
                t = f'{int(h*60)}m ago' if h < 1 else \
                    f'{int(h)}h ago' if h < 24 else \
                    f'{int(h/24)}d ago'
            except Exception:
                t = 'Recent'
            badge = ' ✅' if ver else ''
            popup = (f'<b style="color:{color}">'
                     f'{str(inc_type).upper()}{badge}</b><br>'
                     f'<small>⏱ {t} · 👍 {up} · Sev {sev}/3</small>'
                     + (f'<br><small>{desc[:80]}</small>' if desc else ''))
            folium.CircleMarker([lat, lng], radius=radius,
                                color=color, fill=True, fill_opacity=0.75,
                                popup=folium.Popup(popup, max_width=200)).add_to(cluster)
    return m


def add_routes_to_map(m, safe_route, fast_route):
    if not HAS_FOLIUM or m is None:
        return m
    if safe_route and safe_route.get('points'):
        folium.PolyLine(safe_route['points'], color='#00CC44', weight=5,
                        opacity=0.9, tooltip=f"Safe — {safe_route.get('safety_avg', 70)}/100"
                        ).add_to(m)
    if fast_route and fast_route.get('points'):
        folium.PolyLine(fast_route['points'], color='#FF4444', weight=4,
                        opacity=0.7, dash_array='10',
                        tooltip=f"Fast — {fast_route.get('safety_avg', 50)}/100"
                        ).add_to(m)
    for lat, lng in safe_route.get('danger_zones', []) if safe_route else []:
        folium.CircleMarker([lat, lng], radius=12, color='#FF0000',
                            fill=True, fill_opacity=0.3, popup='Danger Zone').add_to(m)
    return m

