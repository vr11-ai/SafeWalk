# setup_db.py — MEMBER 2 OWNS THIS FILE
import sqlite3
from datetime import datetime, timedelta

def init_database():
    conn = sqlite3.connect('safewalk.db')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        type TEXT,
        severity INTEGER DEFAULT 1,
        time_of_day TEXT,
        city TEXT,
        country TEXT,
        description TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        source TEXT DEFAULT 'user_report',
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        verified BOOLEAN DEFAULT 0,
        weight REAL DEFAULT 1.0
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS session_votes (
        session_id TEXT,
        incident_id INTEGER,
        vote_type TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (session_id, incident_id)
    )
    ''')
    conn.commit()
    conn.close()
    print('Database ready — v2.0 schema with weights.')
    seed_demo_data()

def save_incident(lat, lng, inc_type, severity,
                  time_of_day, city, country, description=''):
    conn = sqlite3.connect('safewalk.db')
    conn.execute('''
    INSERT INTO incidents
    (lat,lng,type,severity,time_of_day,city,country,description,weight)
    VALUES (?,?,?,?,?,?,?,?,1.0)
    ''', (lat,lng,inc_type,severity,time_of_day,city,country,description))
    conn.commit()
    conn.close()

def seed_demo_data():
    """Seeds at least 15 realistic Delhi incidents if table is empty or has fewer than 15 rows."""
    conn = sqlite3.connect('safewalk.db')
    count = conn.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
    if count >= 15:
        conn.close()
        return

    now = datetime.now()
    demo_incidents = [
        # (lat, lng, type, severity, time_of_day, city, country, description, hours_ago, upvotes, downvotes, verified)
        (28.6315, 77.2167, "harassment", 2, "night", "Delhi", "India", "Catcalling and aggressive shouting near CP outer circle block B.", 1.5, 4, 0, 1),
        (28.5535, 77.1945, "following", 2, "night", "Delhi", "India", "Followed by two individuals from HKV parking lot to main road.", 3.0, 3, 0, 1),
        (28.6506, 77.2303, "theft", 1, "evening", "Delhi", "India", "Phone snatched in crowded narrow alley near Chandni Chowk metro gate 3.", 5.5, 2, 0, 0),
        (28.5677, 77.2433, "unsafe_area", 2, "night", "Delhi", "India", "Streetlights non-functional in lane behind Central Market, feels very unsafe.", 8.0, 5, 1, 1),
        (28.5283, 77.2185, "harassment", 3, "night", "Delhi", "India", "Group of intoxicated men blocking pedestrian pathway near Press Enclave road.", 14.0, 6, 0, 1),
        (28.6434, 77.2155, "unsafe_area", 3, "night", "Delhi", "India", "Dark alley with no police visibility near Paharganj main market entrance.", 18.0, 4, 1, 1),
        (28.6521, 77.1906, "theft", 1, "afternoon", "Delhi", "India", "Bag purse snatching reported near Karol Bagh metro station.", 22.0, 1, 0, 0),
        (28.6297, 77.0782, "following", 2, "evening", "Delhi", "India", "Suspicious car slow-following pedestrian near Janakpuri District Centre.", 26.0, 3, 0, 1),
        (28.5823, 77.0500, "unsafe_area", 2, "night", "Delhi", "India", "Completely unlit stretch near Dwarka Sector 10 DDA park.", 32.0, 2, 0, 0),
        (28.7056, 77.1260, "harassment", 2, "evening", "Delhi", "India", "Verbal harassment at bus stop near Rohini Sector 7.", 38.0, 2, 1, 0),
        (28.6675, 77.2285, "harassment", 3, "night", "Delhi", "India", "Aggressive confrontation under the flyover near Kashmere Gate ISBT.", 44.0, 5, 0, 1),
        (28.7077, 77.2064, "unsafe_area", 1, "evening", "Delhi", "India", "Poor lighting and lack of security patrol near student residential lane.", 50.0, 3, 0, 1),
        (28.6469, 77.3160, "theft", 2, "night", "Delhi", "India", "Attempted chain snatching near Anand Vihar foot-over-bridge.", 60.0, 2, 0, 0),
        (28.5482, 77.2426, "following", 1, "night", "Delhi", "India", "Felt stalked walking towards M-block market back gate.", 72.0, 1, 0, 0),
        (28.5494, 77.2514, "unsafe_area", 2, "night", "Delhi", "India", "Isolated subway passage with broken surveillance cameras at Nehru Place.", 84.0, 4, 1, 1),
        (28.5355, 77.1582, "harassment", 2, "night", "Delhi", "India", "Poorly lit service road near Vasant Kunj sector C pocket 9.", 12.0, 3, 0, 1),
        (28.6180, 77.2980, "unsafe_area", 2, "night", "Delhi", "India", "Unlit stretch near Mayur Vihar Phase 1 pocket 1.", 20.0, 4, 0, 1),
        (28.5700, 77.2220, "following", 1, "evening", "Delhi", "India", "Followed from South Extension Part 2 market.", 30.0, 2, 0, 0),
        (28.5175, 77.1812, "unsafe_area", 3, "night", "Delhi", "India", "Deserted dark forest road stretch towards Mehrauli with zero lighting.", 720.0, 3, 0, 1),
    ]

    for lat, lng, inc_type, sev, tod, city, country, desc, h_ago, up, down, ver in demo_incidents:
        ts = (now - timedelta(hours=h_ago)).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
        INSERT INTO incidents
        (lat, lng, type, severity, time_of_day, city, country, description, timestamp, upvotes, downvotes, verified, weight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1.0)
        ''', (lat, lng, inc_type, sev, tod, city, country, desc, ts, up, down, ver))

    conn.commit()
    conn.close()
    print(f'Seeded {len(demo_incidents)} demo incidents for Delhi.')

if __name__ == '__main__':
    init_database()
