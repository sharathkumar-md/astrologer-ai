"""
Simple database for render_deploy
Stores users and conversation history
"""
import sqlite3
import json
from datetime import datetime
import os


class SimpleDatabase:
    def __init__(self, db_name="astra_render.db"):
        """Initialize database in render_deploy folder"""
        # Store DB file in render_deploy directory
        db_path = os.path.join(os.path.dirname(__file__), db_name)
        self.db_name = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                birth_time TEXT NOT NULL,
                birth_location TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                timezone TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Conversations table with session support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conv_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                character_id TEXT,
                language TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Sessions table to track active sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                character_id TEXT,
                language TEXT,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def find_or_create_user(self, name, birth_date, birth_time, birth_location, 
                           latitude=None, longitude=None, timezone=None):
        """Find existing user or create new one based on birth details"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Try to find existing user with same birth details
        cursor.execute('''
            SELECT user_id FROM users 
            WHERE name = ? AND birth_date = ? AND birth_time = ? AND birth_location = ?
        ''', (name, birth_date, birth_time, birth_location))
        
        user = cursor.fetchone()
        
        if user:
            user_id = user[0]
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (name, birth_date, birth_time, birth_location, 
                                 latitude, longitude, timezone, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, birth_date, birth_time, birth_location, 
                  latitude, longitude, timezone, datetime.now().isoformat()))
            user_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return user_id
    
    def create_or_update_session(self, session_id, user_id, character_id, language):
        """Create new session or update existing one"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id, character_id, language, created_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                last_active = ?,
                character_id = ?,
                language = ?
        ''', (session_id, user_id, character_id, language, now, now, now, character_id, language))
        
        conn.commit()
        conn.close()
    
    def add_conversation(self, user_id, session_id, query, response, character_id, language):
        """Add a conversation exchange"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (user_id, session_id, query, response, 
                                     character_id, language, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, session_id, query, response, character_id, language, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_session_history(self, session_id, limit=20):
        """Get conversation history for a specific session"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT query, response, timestamp
            FROM conversations
            WHERE session_id = ?
            ORDER BY conv_id DESC
            LIMIT ?
        ''', (session_id, limit))
        
        conversations = cursor.fetchall()
        conn.close()
        
        # Reverse to get chronological order (oldest to newest)
        conversations.reverse()
        
        # Format as conversation history for LLM
        history = []
        for query, response, timestamp in conversations:
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
        
        return history
    
    def get_user_history(self, user_id, limit=20):
        """Get all conversation history for a user (across sessions)"""
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
        
        # Reverse to get chronological order
        conversations.reverse()
        
        # Format as conversation history
        history = []
        for query, response, timestamp in conversations:
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
        
        return history
    
    def get_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM conversations')
        total_conversations = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_conversations': total_conversations,
            'total_sessions': total_sessions
        }
