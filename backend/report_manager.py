# report_manager.py — MEMBER 2 OWNS THIS FILE (NEW IN v2.0)
import sqlite3
import math
from datetime import datetime

def calculate_weight(hours_ago, upvotes=0, downvotes=0):
    '''
    The weight formula — three factors:
    1. RECENCY: exponential decay (half-life = 48 hours)
       0-6h → ~1.0 (maximum — happening now)
       6-24h → ~0.8 (very recent)
       1-7d → ~0.5 (this week)
       7-30d → ~0.2 (this month)
       30-90d → ~0.05 (historical context)
    2. COMMUNITY TRUST: upvotes boost, downvotes reduce
    3. VERIFIED BONUS: 3+ upvotes = 1.3x multiplier
    '''
    # Factor 1: Recency
    recency = math.exp(-0.693 * hours_ago / 48)

    # Factor 2: Trust modifier
    net = upvotes - downvotes
    if net > 0:
        trust = 1 + (0.1 * min(net, 5))
    elif net < 0:
        trust = max(0.3, 1 + (0.15 * net))
    else:
        trust = 1.0

    # Factor 3: Verified bonus
    verified_bonus = 1.3 if upvotes >= 3 else 1.0

    weight = recency * trust * verified_bonus
    return round(min(2.0, max(0.01, weight)), 3)

def update_all_weights():
    '''Recalculates weights for ALL incidents. Runs in <100ms.'''
    conn = sqlite3.connect('safewalk.db')
    rows = conn.execute(
        'SELECT id, timestamp, upvotes, downvotes FROM incidents'
    ).fetchall()
    now = datetime.now()
    updates = []
    for inc_id, ts_str, up, down in rows:
        try:
            ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            hours_ago = max(0.0, (now - ts).total_seconds() / 3600)
            w = calculate_weight(hours_ago, up or 0, down or 0)
        except Exception:
            w = 0.01
        updates.append((w, inc_id))
    conn.executemany(
        'UPDATE incidents SET weight=? WHERE id=?', updates)
    conn.commit()
    conn.close()

def get_weighted_incidents_near(lat, lng, radius_km=0.3):
    conn = sqlite3.connect('safewalk.db')
    d = radius_km / 111.0
    rows = conn.execute('''
    SELECT id, lat, lng, type, severity,
           timestamp, upvotes, downvotes,
           verified, weight, description
    FROM incidents
    WHERE lat BETWEEN ? AND ?
      AND lng BETWEEN ? AND ?
      AND weight > 0.05
    ORDER BY weight DESC
    ''', (lat - d, lat + d, lng - d, lng + d)).fetchall()
    conn.close()
    return [{'id': r[0], 'lat': r[1], 'lng': r[2], 'type': r[3],
             'severity': r[4], 'timestamp': r[5], 'upvotes': r[6],
             'downvotes': r[7], 'verified': r[8],
             'weight': r[9], 'description': r[10]} for r in rows]

def upvote_incident(incident_id, session_id):
    conn = sqlite3.connect('safewalk.db')
    try:
        conn.execute('''INSERT INTO session_votes
        (session_id, incident_id, vote_type) VALUES (?, ?, "up")''',
        (session_id, incident_id))
        conn.execute('''UPDATE incidents SET
        upvotes = upvotes + 1,
        verified = CASE WHEN upvotes + 1 >= 3 THEN 1 ELSE 0 END
        WHERE id = ?''', (incident_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def downvote_incident(incident_id, session_id):
    conn = sqlite3.connect('safewalk.db')
    try:
        conn.execute('''INSERT INTO session_votes
        (session_id, incident_id, vote_type) VALUES (?, ?, "down")''',
        (session_id, incident_id))
        conn.execute('''UPDATE incidents SET
        downvotes = downvotes + 1
        WHERE id = ?''', (incident_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_recent_reports_in_city(city, limit=8):
    conn = sqlite3.connect('safewalk.db')
    rows = conn.execute('''
    SELECT id, type, severity, timestamp,
           upvotes, verified, description, lat, lng
    FROM incidents
    WHERE city=? ORDER BY timestamp DESC LIMIT ?
    ''', (city, limit)).fetchall()
    conn.close()
    return rows

def get_city_stats(city):
    conn = sqlite3.connect('safewalk.db')
    s = conn.execute('''
    SELECT COUNT(*),
           SUM(CASE WHEN (julianday("now") - julianday(timestamp)) * 24 <= 24
               THEN 1 ELSE 0 END),
           SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END),
           AVG(severity)
    FROM incidents WHERE city=? AND weight > 0.05
    ''', (city,)).fetchone()
    conn.close()
    if not s or s[0] is None:
        return {'total': 0, 'last_24h': 0, 'verified': 0, 'avg_severity': 0.0}
    return {
        'total': s[0] or 0,
        'last_24h': s[1] or 0,
        'verified': s[2] or 0,
        'avg_severity': round(s[3] or 0, 1)
    }
