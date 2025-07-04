import sqlite3

DATABASE = 'mood_tracker.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Added user_id column if it doesn't exist, and made it NOT NULL
    # If you already have data, you might need to handle existing rows
    # by adding a default user_id or migrating data.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS moods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            emoji TEXT NOT NULL,
            name TEXT NOT NULL,
            reason TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_mood(user_id, emoji, name, reason, timestamp):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO moods (user_id, emoji, name, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (user_id, emoji, name, reason, timestamp))
    conn.commit()
    conn.close()

def get_all_moods(user_id):
    """
    Retrieves all moods for a specific user.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Filter by user_id
    cursor.execute("SELECT id, user_id, emoji, name, reason, timestamp FROM moods WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    moods = cursor.fetchall()
    conn.close()
    # Convert list of tuples to list of dictionaries for easier JSON serialization
    return [{'id': m[0], 'user_id': m[1], 'emoji': m[2], 'name': m[3], 'reason': m[4], 'timestamp': m[5]} for m in moods]

def get_mood_by_id(mood_id, user_id):
    """
    Retrieves a single mood by ID, ensuring it belongs to the specified user.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Filter by mood_id AND user_id
    cursor.execute("SELECT id, user_id, emoji, name, reason, timestamp FROM moods WHERE id = ? AND user_id = ?", (mood_id, user_id))
    mood = cursor.fetchone()
    conn.close()
    if mood:
        return {'id': mood[0], 'user_id': mood[1], 'emoji': mood[2], 'name': mood[3], 'reason': mood[4], 'timestamp': mood[5]}
    return None

def delete_mood(mood_id, user_id):
    """
    Deletes a mood by ID, ensuring it belongs to the specified user.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Filter by mood_id AND user_id
    cursor.execute("DELETE FROM moods WHERE id = ? AND user_id = ?", (mood_id, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def edit_mood(mood_id, user_id, name, emoji, reason):
    """
    Edits a mood by ID, ensuring it belongs to the specified user.
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Filter by mood_id AND user_id
    cursor.execute("UPDATE moods SET name = ?, emoji = ?, reason = ? WHERE id = ? AND user_id = ?",
                   (name, emoji, reason, mood_id, user_id))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0
