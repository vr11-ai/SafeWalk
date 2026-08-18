# map_builder.py - Map Builder Engine with Folium, HeatMap, and Markers
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [BASE_DIR, os.path.join(BASE_DIR, 'backend'), os.path.join(BASE_DIR, 'ai_backend'), os.path.dirname(os.path.abspath(__file__))]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from report_manager import update_all_weights
except ImportError:
    def update_all_weights():
        pass


def build_safety_map(center=[28.6139, 77.2090], zoom=13):
    if not HAS_FOLIUM:
        return None

    try:
        update_all_weights()
    except Exception:
        pass

    m = folium.Map(location=center, zoom_start=zoom, tiles='CartoDB dark_matter')

    db_path = os.path.join(BASE_DIR, 'backend', 'safewalk.db')
    if not os.path.exists(db_path):
        db_path = os.path.join(BASE_DIR, 'safewalk.db')
    if not os.path.exists(db_path):
        db_path = 'safewalk.db'

    rows = []
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute('''
            SELECT lat, lng, severity, type, timestamp,
                   upvotes, verified, weight, description, id
            FROM incidents WHERE weight > 0.05
            ORDER BY weight DESC
        ''').fetchall()
        conn.close()
    except Exception:
        rows = []

    now = datetime.now()
    if rows:
        HeatMap([[r[0], r[1], r[7]] for r in rows],
                gradient={0.2: '#10B981', 0.5: '#F59E0B', 0.8: '#EF4444', 1.0: '#991B1B'},
                radius=25, blur=15, min_opacity=0.3).add_to(m)
        
        cluster = MarkerCluster().add_to(m)
        for lat, lng, sev, inc_type, ts_str, up, ver, wt, desc, inc_id in rows:
            color = 'red' if sev == 3 else 'orange' if sev == 2 else 'yellow'
            wt_val = float(wt) if wt is not None else 1.0
            radius = max(6, min(16, int(wt_val * 12)))
            try:
                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                h = (now - ts).total_seconds() / 3600
                t = f'{int(h*60)}m ago' if h < 1 else f'{int(h)}h ago' if h < 24 else f'{int(h/24)}d ago'
            except Exception:
                t = 'Recent'
            badge = ' ✔ Verified' if ver else ''
            popup_html = (f'<div style="font-family:sans-serif; font-size:12px;">'
                          f'<b style="color:{color}; font-size:14px;">{str(inc_type).upper()}{badge}</b><br>'
                          f'<span>🕒 {t} • 👍 {up} • Severity: {sev}/3</span>'
                          + (f'<br><small style="color:#555;">{desc[:100]}</small>' if desc else '')
                          + '</div>')
            folium.CircleMarker([lat, lng], radius=radius,
                                color=color, fill=True, fill_color=color, fill_opacity=0.75,
                                popup=folium.Popup(popup_html, max_width=220)).add_to(cluster)
    return m


def add_routes_to_map(m, safe_route, fast_route):
    if not HAS_FOLIUM or m is None:
        return m

    # Safest Route (Green)
    if safe_route and safe_route.get('points'):
        pts = safe_route['points']
        folium.PolyLine(pts, color='#10B981', weight=6, opacity=0.9,
                        tooltip=f"🟢 Safest Route ({safe_route.get('safety_avg', 70)}/100)"
                        ).add_to(m)
        # Start & End markers
        folium.Marker(pts[0], popup="Start Location", icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker(pts[-1], popup="Destination", icon=folium.Icon(color="blue", icon="flag")).add_to(m)

    # Fastest Route (Red Dashed)
    if fast_route and fast_route.get('points') and fast_route != safe_route:
        folium.PolyLine(fast_route['points'], color='#EF4444', weight=4, opacity=0.7, dash_array='10',
                        tooltip=f"🔴 Fastest Route ({fast_route.get('safety_avg', 50)}/100)"
                        ).add_to(m)

    # Danger Zones
    for lat, lng in safe_route.get('danger_zones', []) if safe_route else []:
        folium.CircleMarker([lat, lng], radius=14, color='#EF4444',
                            fill=True, fill_color='#EF4444', fill_opacity=0.4,
                            popup='⚠️ High Risk / Danger Zone').add_to(m)
    return m
