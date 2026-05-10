import sqlite3
import os
import sys
import time
from pathlib import Path

class StatsManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            if getattr(sys, 'frozen', False):
                db_path = os.path.join(os.path.dirname(sys.executable), "stats.db")
            else:
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stats.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_path TEXT,
                    artist TEXT,
                    album TEXT,
                    title TEXT,
                    timestamp INTEGER,
                    duration_listened REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artist ON play_history(artist)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_album ON play_history(album)")

    def log_play(self, track_path: str, artist: str, album: str, title: str, duration: float):
        if duration < 5: return # Don't log if listened less than 5 seconds
        
        # De-duplication check: Don't log if same track and duration was logged in last 2 seconds
        now = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM play_history WHERE track_path = ? AND ABS(duration_listened - ?) < 0.1 AND timestamp > ? LIMIT 1",
                (track_path, duration, now - 2)
            )
            if cursor.fetchone():
                return

            conn.execute(
                "INSERT INTO play_history (track_path, artist, album, title, timestamp, duration_listened) VALUES (?, ?, ?, ?, ?, ?)",
                (track_path, artist, album, title, now, duration)
            )

    def get_top_artists(self, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT artist, COUNT(*) as play_count, SUM(duration_listened) as total_time
                FROM play_history 
                WHERE artist != 'Unknown Artist'
                GROUP BY artist 
                ORDER BY total_time DESC 
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_top_albums(self, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT album, artist, COUNT(*) as play_count, SUM(duration_listened) as total_time
                FROM play_history 
                WHERE album != 'Unknown Album'
                GROUP BY album, artist 
                ORDER BY total_time DESC 
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_total_listening_time(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT SUM(duration_listened) FROM play_history")
            res = cursor.fetchone()[0]
            return res if res else 0.0

    def get_recent_history(self, limit=20):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT title, artist, timestamp 
                FROM play_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()
