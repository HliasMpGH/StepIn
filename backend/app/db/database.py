import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

from app.core.config import settings

class Database:
    def __init__(self):
        # Check if we're using PostgreSQL or SQLite
        self.use_postgres = settings.USE_POSTGRES

        if self.use_postgres:
            # PostgreSQL connection
            self.conn = psycopg2.connect(
                host=settings.DB_HOST,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                cursor_factory=RealDictCursor
            )
        else:
            # SQLite connection
            self.conn = sqlite3.connect(
                settings.DB_PATH,
                check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row

        self.create_tables()

    def create_tables(self):
        """Create database tables if they don't exist"""
        if self.use_postgres:
            self._create_tables_postgres()
        else:
            self._create_tables_sqlite()

    def _create_tables_postgres(self):
        """Create tables for PostgreSQL"""
        with self.conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    age SMALLINT CHECK (age > 0),
                    gender VARCHAR(50)
                )
            """)

            # Create meetings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    meeting_id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    t1 TIMESTAMP WITH TIME ZONE NOT NULL,
                    t2 TIMESTAMP WITH TIME ZONE NOT NULL,
                    lat FLOAT NOT NULL,
                    long FLOAT NOT NULL,
                    participants TEXT NOT NULL
                )
            """)

            # Create log table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    meeting_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action SMALLINT NOT NULL CHECK (action IN (1, 2, 3)),
                    FOREIGN KEY (email) REFERENCES users(email),
                    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id)
                )
            """)

            # Create chat messages table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    meeting_id INTEGER NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
                    FOREIGN KEY (email) REFERENCES users(email)
                )
            """)

            self.conn.commit()

    def _create_tables_sqlite(self):
        """Create tables for SQLite"""
        with self.conn:
            # Create users table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT
                )
            """)

            # Create meetings table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS meetings (
                    meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    t1 TIMESTAMP NOT NULL,
                    t2 TIMESTAMP NOT NULL,
                    lat REAL NOT NULL,
                    long REAL NOT NULL,
                    participants TEXT NOT NULL
                )
            """)

            # Create log table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    meeting_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action INTEGER NOT NULL,
                    FOREIGN KEY (email) REFERENCES users(email),
                    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id)
                )
            """)

            # Create chat messages table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
                    FOREIGN KEY (email) REFERENCES users(email)
                )
            """)

    def add_user(self, email, name, age, gender):
        """Add a new user to the database"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, name, age, gender) VALUES (%s, %s, %s, %s)",
                    (email, name, age, gender)
                )
                self.conn.commit()
        else:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO users (email, name, age, gender) VALUES (?, ?, ?, ?)",
                    (email, name, age, gender)
                )

    def delete_user(self, email):
        """Delete a user from the database"""
        # First check if the user exists
        user = self.get_user(email)
        if not user:
            return None

        try:
            if self.use_postgres:
                with self.conn.cursor() as cur:
                    # Delete the user
                    cur.execute("DELETE FROM users WHERE email = %s", (email,))
                    self.conn.commit()
            else:
                with self.conn:
                    self.conn.execute("DELETE FROM users WHERE email = ?", (email,))
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return {"error": f"Database error: {str(e)}"}

    def get_user(self, email):
        """Get user details by email"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if user:
                    return dict(user)
                return None
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user:
                return {
                    "email": user["email"],
                    "name": user["name"],
                    "age": user["age"],
                    "gender": user["gender"]
                }
            return None

    def add_meeting(self, title, description, t1, t2, lat, long, participants):
        """Add a new meeting"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO meetings
                       (title, description, t1, t2, lat, long, participants)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING meeting_id""",
                    (title, description, t1, t2, lat, long, participants)
                )
                meeting_id = cur.fetchone()["meeting_id"]
                self.conn.commit()
                return meeting_id
        else:
            cursor = self.conn.cursor()
            with self.conn:
                cursor.execute(
                    """INSERT INTO meetings
                       (title, description, t1, t2, lat, long, participants)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (title, description, t1, t2, lat, long, participants)
                )
                return cursor.lastrowid

    def delete_meeting(self, meeting_id):
        """Delete a meeting from the database"""
        # First check if the meeting exists
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            return None

        try:
            if self.use_postgres:
                with self.conn.cursor() as cur:
                    # Delete the meeting
                    cur.execute("DELETE FROM meetings WHERE meeting_id = %s", (meeting_id,))
                    self.conn.commit()
            else:
                with self.conn:
                    self.conn.execute("DELETE FROM meetings WHERE meeting_id = ?", (meeting_id,))
            return True
        except Exception as e:
            print(f"Error deleting meeting: {e}")
        return {"error": f"Database error: {str(e)}"}

    def get_meetings_by_user(self, email: str):
        """
        Return all meetings where participants column contains the email.
        """
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT meeting_id, title, description, t1, t2, lat, long, participants"
                    " FROM meetings"
                    " WHERE participants LIKE %s",
                    (f"%{email}%",)
                )
                return [dict(row) for row in cur.fetchall()]
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT meeting_id, title, description, t1, t2, lat, long, participants"
                " FROM meetings"
                " WHERE participants LIKE ?",
                (f"%{email}%",)
            )
            rows = cursor.fetchall()
            return [
                {
                    "meeting_id": r["meeting_id"],
                    "title": r["title"],
                    "description": r["description"],
                    "t1": r["t1"],
                    "t2": r["t2"],
                    "lat": r["lat"],
                    "long": r["long"],
                    "participants": r["participants"]
                }
                for r in rows
            ]

    def get_meeting(self, meeting_id):
        """Get meeting details by ID"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute("SELECT * FROM meetings WHERE meeting_id = %s", (meeting_id,))
                meeting = cur.fetchone()
                if meeting:
                    return dict(meeting)
                return None
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM meetings WHERE meeting_id = ?", (meeting_id,))
            meeting = cursor.fetchone()
            if meeting:
                return {
                    "meeting_id": meeting["meeting_id"],
                    "title": meeting["title"],
                    "description": meeting["description"],
                    "t1": meeting["t1"],
                    "t2": meeting["t2"],
                    "lat": meeting["lat"],
                    "long": meeting["long"],
                    "participants": meeting["participants"]
                }
            return None

    def get_active_meetings(self):
        """Get list of active meeting IDs"""
        current_time = datetime.now(timezone.utc)#.isoformat()
        print(f"Current time for active meetings check: {current_time}")

        # We'll extend meeting activation for 2 hours after creation
        # by using only t1 for "active" status check
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT meeting_id FROM meetings
                    WHERE t1 <= %s AND t2 >= %s""",
                    (current_time, current_time)
                )
                result = [row["meeting_id"] for row in cur.fetchall()]
                print(f"PostgreSQL active meetings: {result}")
                return result
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT meeting_id, title, t1, t2 FROM meetings
                WHERE t1 <= ? AND t2 >= ?""",
                (current_time, current_time)
            )
            rows = cursor.fetchall()

            # Debug output
            for row in rows:
                print(f"Meeting {row['meeting_id']} ({row['title']}): t1={row['t1']}, t2={row['t2']}")

            result = [row["meeting_id"] for row in rows]
            print(f"SQLite active meetings: {result}")
            return result

    def log_action(self, email, meeting_id, action):
        """Log a user action for a meeting"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO logs (email, meeting_id, action) VALUES (%s, %s, %s)",
                    (email, meeting_id, action)
                )
                self.conn.commit()
                return True
        else:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO logs (email, meeting_id, action) VALUES (?, ?, ?)",
                    (email, meeting_id, action)
                )
                return True

    def save_chat_message(self, meeting_id, email, message):
        """Save a chat message"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_messages (meeting_id, email, message) VALUES (%s, %s, %s)",
                    (meeting_id, email, message)
                )
                self.conn.commit()
                return True
        else:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO chat_messages (meeting_id, email, message) VALUES (?, ?, ?)",
                    (meeting_id, email, message)
                )
                return True

    def get_meeting_messages(self, meeting_id):
        """Get all messages for a meeting"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT email, message, timestamp FROM chat_messages
                       WHERE meeting_id = %s ORDER BY timestamp""",
                    (meeting_id,)
                )
                return [dict(row) for row in cur.fetchall()]
        else:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT email, message, timestamp FROM chat_messages
                   WHERE meeting_id = ? ORDER BY timestamp""",
                (meeting_id,)
            )
            return [{"email": row["email"], "message": row["message"], "timestamp": row["timestamp"]}
                    for row in cursor.fetchall()]

    def get_user_messages(self, email, meeting_id=None):
        """Get all messages by a user (optionally for a specific meeting)"""
        if self.use_postgres:
            with self.conn.cursor() as cur:
                if meeting_id:
                    cur.execute(
                        """SELECT meeting_id, message, timestamp FROM chat_messages
                           WHERE email = %s AND meeting_id = %s ORDER BY timestamp""",
                        (email, meeting_id)
                    )
                else:
                    cur.execute(
                        """SELECT meeting_id, message, timestamp FROM chat_messages
                           WHERE email = %s ORDER BY timestamp""",
                        (email,)
                    )
                return [dict(row) for row in cur.fetchall()]
        else:
            cursor = self.conn.cursor()
            if meeting_id:
                cursor.execute(
                    """SELECT meeting_id, message, timestamp FROM chat_messages
                       WHERE email = ? AND meeting_id = ? ORDER BY timestamp""",
                    (email, meeting_id)
                )
            else:
                cursor.execute(
                    """SELECT meeting_id, message, timestamp FROM chat_messages
                       WHERE email = ? ORDER BY timestamp""",
                    (email,)
                )
            return [{"meeting_id": row["meeting_id"], "message": row["message"], "timestamp": row["timestamp"]}
                    for row in cursor.fetchall()]


# Database singleton
_db_instance = None

def get_database():
    """Get or create the database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance