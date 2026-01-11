import sqlite3
import json
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class UserDatabase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                birth_time TEXT NOT NULL,
                birth_location TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone TEXT NOT NULL,
                natal_chart TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_user(self, name, birth_date, birth_time, birth_location, latitude, longitude, timezone, natal_chart):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, birth_date, birth_time, birth_location, latitude, longitude, timezone, natal_chart, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, birth_date, birth_time, birth_location, latitude, longitude, timezone, json.dumps(natal_chart), datetime.now().isoformat()))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def list_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, birth_date FROM users')
        users = cursor.fetchall()
        conn.close()
        return users
    
    def add_conversation(self, user_id, query, response):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (user_id, query, response, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, query, response, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, user_id, limit=20):
        """Get the last N messages for a user (default 20)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT query, response, timestamp
            FROM conversations
            WHERE user_id = ?
            ORDER BY conv_id DESC
            LIMIT ?
        ''', (user_id, limit))
        conversations = cursor.fetchall()
        conn.close()

        # Reverse to get chronological order (oldest to newest)
        conversations.reverse()

        # Format as conversation history
        history = []
        for query, response, timestamp in conversations:
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})

        return history

    def get_session_history(self, user_id, session_id, limit=20):
        """
        Get conversation history for a SPECIFIC SESSION only

        Args:
            user_id: User ID
            session_id: Session ID to filter by
            limit: Maximum number of messages

        Returns:
            List of messages for current session only
        """
        # SQLite version doesn't have session_id column in conversations table
        # Return empty list to force fresh start for new chats
        # This is acceptable since SQLite is fallback/development mode
        return []
    