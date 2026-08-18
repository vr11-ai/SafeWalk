# setup_db.py — MEMBER 2 OWNS THIS FILE
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'safewalk.db')


def init_database(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
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


def save_incident(lat, lng, inc_type, severity,
                  time_of_day, city, country, description='', db_path=DB_PATH):
    init_database(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute('''
    INSERT INTO incidents
    (lat,lng,type,severity,time_of_day,city,country,description,weight)
    VALUES (?,?,?,?,?,?,?,?,1.0)
    ''', (lat, lng, inc_type, severity, time_of_day, city, country, description))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_database()
