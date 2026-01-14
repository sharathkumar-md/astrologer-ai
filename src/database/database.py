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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                emoji TEXT DEFAULT '✨',
                about TEXT,
                age INTEGER,
                experience INTEGER,
                specialty TEXT,
                language_style TEXT DEFAULT 'casual',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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

    # ==================== CHARACTER MANAGEMENT ====================

    def add_character(self, character_id, name, emoji='✨', about=None, age=None,
                     experience=None, specialty=None, language_style='casual'):
        """Add a new character to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO characters (character_id, name, emoji, about, age, experience, specialty, language_style)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (character_id, name, emoji, about, age, experience, specialty, language_style))
            conn.commit()
            logger.info(f"Added character: {character_id} - {name}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Character {character_id} already exists")
            return False
        finally:
            conn.close()

    def update_character(self, character_id, **kwargs):
        """Update character fields"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Build dynamic update query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'emoji', 'about', 'age', 'experience', 'specialty', 'language_style', 'is_active']:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            conn.close()
            return False

        values.append(datetime.now().isoformat())
        values.append(character_id)

        query = f"UPDATE characters SET {', '.join(fields)}, updated_at = ? WHERE character_id = ?"
        cursor.execute(query, values)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        if updated:
            logger.info(f"Updated character: {character_id}")
        return updated

    def get_character(self, character_id):
        """Get a single character by ID"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM characters WHERE character_id = ?', (character_id,))
        character = cursor.fetchone()
        conn.close()

        if character:
            return dict(character)
        return None

    def get_all_characters(self, active_only=True):
        """Get all characters from database"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if active_only:
            cursor.execute('SELECT * FROM characters WHERE is_active = 1 ORDER BY name')
        else:
            cursor.execute('SELECT * FROM characters ORDER BY name')

        characters = cursor.fetchall()
        conn.close()

        return [dict(char) for char in characters]

    def activate_character(self, character_id):
        """Activate a character"""
        return self.update_character(character_id, is_active=1)

    def deactivate_character(self, character_id):
        """Deactivate a character"""
        return self.update_character(character_id, is_active=0)

    def delete_character(self, character_id):
        """Delete a character from database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM characters WHERE character_id = ?', (character_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()

        if deleted:
            logger.info(f"Deleted character: {character_id}")
        return deleted
    