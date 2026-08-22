import os
# report_manager.py - Real-Time Dynamic Weight Engine (Security Hardened DB Contexts)
import sqlite3
import math
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "safewalk.db")


def calculate_weight(hours_ago: float, upvotes: int = 0, downvotes: int = 0) -> float:
    """
    Calculates dynamic incident weight using 3 factors:
    1. Recency Decay (exponential 48-hour half-life)
    2. Community Trust Modifier
    3. Verified Bonus (3+ upvotes = 1.3x multiplier)
    """
    recency = math.exp(-0.693 * hours_ago / 48)

    net = upvotes - downvotes
    if net > 0:
        trust = 1.0 + (0.1 * min(net, 5))
    elif net < 0:
        trust = max(0.3, 1.0 + (0.15 * net))
    else:
        trust = 1.0

    verified_bonus = 1.3 if upvotes >= 3 else 1.0

    weight = recency * trust * verified_bonus
    return round(min(2.0, max(0.01, weight)), 3)


def update_all_weights():
    """Recalculates weights for ALL incidents using safe context manager."""
    try:
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            rows = conn.execute('SELECT id, timestamp, upvotes, downvotes FROM incidents').fetchall()
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
            conn.executemany('UPDATE incidents SET weight=? WHERE id=?', updates)
    except Exception as e:
        print(f"Weight update error: {e}")


def get_weighted_incidents_near(lat: float, lng: float, radius_km: float = 0.3):
    d = radius_km / 111.0
    try:
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            query = """
            SELECT id, lat, lng, type, severity,
                   timestamp, upvotes, downvotes,
                   verified, weight, description
            FROM incidents
            WHERE lat BETWEEN ? AND ?
              AND lng BETWEEN ? AND ?
              AND weight > 0.05
            ORDER BY weight DESC
            """
            rows = conn.execute(query, (lat - d, lat + d, lng - d, lng + d)).fetchall()
            return [{'id': r[0], 'lat': r[1], 'lng': r[2], 'type': r[3],
                     'severity': r[4], 'timestamp': r[5], 'upvotes': r[6],
                     'downvotes': r[7], 'verified': r[8],
                     'weight': r[9], 'description': r[10]} for r in rows]
    except Exception as e:
        print(f"Fetch incidents error: {e}")
        return []


def upvote_incident(incident_id: int, session_id: str) -> bool:
    try:
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            conn.execute(
                'INSERT INTO session_votes (session_id, incident_id, vote_type) VALUES (?, ?, "up")',
                (session_id, incident_id)
            )
            conn.execute(
                'UPDATE incidents SET upvotes = upvotes + 1, verified = CASE WHEN upvotes + 1 >= 3 THEN 1 ELSE 0 END WHERE id = ?',
                (incident_id,)
            )
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Upvote error: {e}")
        return False


def downvote_incident(incident_id: int, session_id: str) -> bool:
    try:
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            conn.execute(
                'INSERT INTO session_votes (session_id, incident_id, vote_type) VALUES (?, ?, "down")',
                (session_id, incident_id)
            )
            conn.execute(
                'UPDATE incidents SET downvotes = downvotes + 1 WHERE id = ?',
                (incident_id,)
            )
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Downvote error: {e}")
        return False


def get_recent_reports_in_city(city: str, limit: int = 8):
    try:
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            query = """
            SELECT id, type, severity, timestamp,
                   upvotes, verified, description, lat, lng
            FROM incidents
            WHERE city=? ORDER BY timestamp DESC LIMIT ?
            """
            return conn.execute(query, (city, limit)).fetchall()
    except Exception as e:
        print(f"Fetch city reports error: {e}")
        return []


def get_city_stats(city: str):
    try:
        with sqlite3.connect(DB_PATH, timeout=10.0) as conn:
            query = """
            SELECT COUNT(*),
                   SUM(CASE WHEN (julianday("now") - julianday(timestamp)) * 24 <= 24
                       THEN 1 ELSE 0 END),
                   SUM(CASE WHEN verified = 1 THEN 1 ELSE 0 END),
                   AVG(severity)
            FROM incidents WHERE city=? AND weight > 0.05
            """
            s = conn.execute(query, (city,)).fetchone()
            if not s or s[0] is None:
                return {'total': 0, 'last_24h': 0, 'verified': 0, 'avg_severity': 0.0}
            return {
                'total': s[0] or 0,
                'last_24h': s[1] or 0,
                'verified': s[2] or 0,
                'avg_severity': round(s[3] or 0, 1)
            }
    except Exception as e:
        print(f"City stats error: {e}")
        return {'total': 0, 'last_24h': 0, 'verified': 0, 'avg_severity': 0.0}
