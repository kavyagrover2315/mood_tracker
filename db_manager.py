import sqlite3
from typing import List, Dict, Optional

DATABASE = 'moodmate.db'

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a new SQLite database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable name-based access to columns
    return conn

def init_db() -> None:
    """Initializes users and moods tables if they do not exist."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                age INTEGER,
                gender TEXT,
                email TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS moods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                emoji TEXT,
                name TEXT,
                reason TEXT,
                timestamp TEXT NOT NULL
            )
        ''')

def add_mood(user_id: int, emoji: str, name: str, reason: str, timestamp: str) -> None:
    """Inserts a new mood entry for the specified user."""
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO moods (user_id, emoji, name, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, emoji, name, reason, timestamp)
        )

def get_all_moods() -> List[Dict]:
    """Fetches all moods sorted by latest timestamp (for timeline)."""
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, user_id, emoji, name, reason, timestamp FROM moods ORDER BY timestamp DESC"
        ).fetchall()
    return [dict(row) for row in rows]

def get_mood_by_id(mood_id: int) -> Optional[Dict]:
    """Fetches a single mood entry by its ID."""
    with get_db_connection() as conn:
        mood = conn.execute(
            "SELECT * FROM moods WHERE id = ?", (mood_id,)
        ).fetchone()
    return dict(mood) if mood else None

def delete_mood(mood_id: int) -> bool:
    """Deletes a mood entry by its ID. Returns True if successful."""
    with get_db_connection() as conn:
        result = conn.execute(
            "DELETE FROM moods WHERE id = ?", (mood_id,)
        )
    return result.rowcount > 0

def edit_mood(mood_id: int, name: str, emoji: str, reason: str) -> bool:
    """Updates an existing mood entry."""
    with get_db_connection() as conn:
        result = conn.execute(
            "UPDATE moods SET name = ?, emoji = ?, reason = ? WHERE id = ?",
            (name, emoji, reason, mood_id)
        )
    return result.rowcount > 0
