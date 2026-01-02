"""
PostgreSQL Database Adapter for ASTRA Memory System
Provides PostgreSQL support with fallback to SQLite for development
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

from src.utils.logger import setup_logger

logger = setup_logger(__name__)



class PostgreSQLDatabase:
    """
    PostgreSQL database adapter for ASTRA with OpenAI caching optimization
    """

    def __init__(self, connection_url: str, min_conn=1, max_conn=10):
        """
        Initialize PostgreSQL connection pool

        Args:
            connection_url: PostgreSQL connection URL from Render
            min_conn: Minimum connections in pool
            max_conn: Maximum connections in pool
        """
        self.connection_url = connection_url
        try:
            self.pool = SimpleConnectionPool(
                min_conn,
                max_conn,
                connection_url
            )
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error("Failed to create PostgreSQL connection pool: {e}")
            raise

    def _get_conn(self):
        """Get connection from pool"""
        return self.pool.getconn()

    def _put_conn(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)

    def init_db(self):
        """Initialize database schema from schema.sql"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Read and execute schema file
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            cursor.execute(schema_sql)
            conn.commit()
            logger.info("Database schema initialized successfully")

        except Exception as e:
            conn.rollback()
            logger.error("Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            self._put_conn(conn)

    # ==================================================================
    # USER MANAGEMENT
    # ==================================================================

    def add_user(self, name: str, birth_date: str, birth_time: str,
                 birth_location: str, latitude: float, longitude: float,
                 timezone: str, natal_chart: dict) -> int:
        """
        Add new user to database

        Args:
            name: User's name
            birth_date: Birth date (DD/MM/YYYY format from frontend)
            birth_time: Birth time (HH:MM format)
            birth_location: Birth location string
            latitude: Birth location latitude
            longitude: Birth location longitude
            timezone: Timezone string
            natal_chart: Natal chart data as dictionary

        Returns:
            user_id: New user's ID
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Convert DD/MM/YYYY to YYYY-MM-DD for PostgreSQL DATE type
            day, month, year = birth_date.split('/')
            pg_birth_date = f"{year}-{month}-{day}"

            query = """
            INSERT INTO users (
                name, birth_date, birth_time, birth_location,
                latitude, longitude, timezone, natal_chart
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id
            """

            cursor.execute(query, (
                name, pg_birth_date, birth_time, birth_location,
                latitude, longitude, timezone, Json(natal_chart)
            ))

            user_id = cursor.fetchone()[0]
            conn.commit()

            # Create user profile
            self._create_user_profile(cursor, user_id, conn)

            logger.info("User created with ID: {user_id}")
            return user_id

        except Exception as e:
            conn.rollback()
            logger.error("Error adding user: {e}")
            raise
        finally:
            cursor.close()
            self._put_conn(conn)

    def _create_user_profile(self, cursor, user_id: int, conn):
        """Create initial user profile"""
        query = """
        INSERT INTO user_profiles (user_id, preferred_language, interaction_count)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING
        """
        cursor.execute(query, (user_id, 'hinglish', 0))
        conn.commit()

    def get_user(self, user_id: int) -> Optional[tuple]:
        """
        Get user by ID

        Returns:
            User tuple matching SQLite format for compatibility
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            query = """
            SELECT user_id, name, birth_date, birth_time, birth_location,
                   latitude, longitude, timezone, natal_chart, created_at
            FROM users WHERE user_id = %s
            """

            cursor.execute(query, (user_id,))
            user = cursor.fetchone()

            if user:
                # Convert birth_date back to DD/MM/YYYY format for compatibility
                user_list = list(user)
                if user_list[2]:  # birth_date
                    date_obj = user_list[2]
                    user_list[2] = date_obj.strftime('%d/%m/%Y')

                # Convert JSONB to string for compatibility with existing code
                if user_list[8]:  # natal_chart
                    user_list[8] = json.dumps(user_list[8])

                return tuple(user_list)

            return None

        finally:
            cursor.close()
            self._put_conn(conn)

    def list_users(self) -> List[tuple]:
        """List all users (user_id, name, birth_date)"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            query = """
            SELECT user_id, name, birth_date
            FROM users
            ORDER BY created_at DESC
            """

            cursor.execute(query)
            users = cursor.fetchall()

            # Convert birth_date to DD/MM/YYYY format
            formatted_users = []
            for user in users:
                user_list = list(user)
                if user_list[2]:  # birth_date
                    date_obj = user_list[2]
                    user_list[2] = date_obj.strftime('%d/%m/%Y')
                formatted_users.append(tuple(user_list))

            return formatted_users

        finally:
            cursor.close()
            self._put_conn(conn)

    # ==================================================================
    # CONVERSATION MANAGEMENT
    # ==================================================================

    def add_conversation(self, user_id: int, query: str, response: str,
                        session_id: str = None):
        """
        Add conversation messages (user query + assistant response)

        Args:
            user_id: User ID
            query: User's query
            response: Assistant's response
            session_id: Session identifier (generated if not provided)
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            # Generate session ID if not provided
            if not session_id:
                session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Insert user message
            query_sql = """
            INSERT INTO conversations (user_id, session_id, role, content, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(query_sql, (user_id, session_id, 'user', query))

            # Insert assistant message
            cursor.execute(query_sql, (user_id, session_id, 'assistant', response))

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error("Error adding conversation: {e}")
            raise
        finally:
            cursor.close()
            self._put_conn(conn)

    def get_conversation_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """
        Get recent conversation history formatted for LLM

        Args:
            user_id: User ID
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dicts with 'role' and 'content'
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT role, content, timestamp
            FROM conversations
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """

            cursor.execute(query, (user_id, limit))
            messages = cursor.fetchall()

            # Reverse to get chronological order (oldest to newest)
            messages.reverse()

            # Format for LLM
            history = []
            for msg in messages:
                history.append({
                    "role": msg['role'],
                    "content": msg['content']
                })

            return history

        finally:
            cursor.close()
            self._put_conn(conn)

    def get_recent_messages(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Alias for get_conversation_history for compatibility"""
        return self.get_conversation_history(user_id, limit)

    # ==================================================================
    # USER FACTS (Long-term Memory)
    # ==================================================================

    def add_user_fact(self, user_id: int, fact_type: str, category: str,
                     fact_text: str, fact_summary: str = None,
                     fact_timeframe: str = None, confidence: float = 0.8,
                     importance: float = 0.7, source_conv_id: int = None) -> int:
        """Add extracted fact about user"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            query = """
            INSERT INTO user_facts (
                user_id, fact_type, category, fact_text, fact_summary,
                fact_timeframe, source_conversation_id, confidence_score,
                importance_score, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
            RETURNING fact_id
            """

            cursor.execute(query, (
                user_id, fact_type, category, fact_text, fact_summary,
                fact_timeframe, source_conv_id, confidence, importance
            ))

            fact_id = cursor.fetchone()[0]
            conn.commit()
            return fact_id

        except Exception as e:
            conn.rollback()
            logger.error("Error adding user fact: {e}")
            raise
        finally:
            cursor.close()
            self._put_conn(conn)

    def get_user_facts(self, user_id: int, category: str = None,
                      limit: int = 15) -> List[Dict]:
        """
        Get important facts about user

        Args:
            user_id: User ID
            category: Filter by category (optional)
            limit: Maximum number of facts

        Returns:
            List of fact dictionaries
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if category:
                query = """
                SELECT fact_id, fact_type, category, fact_text, fact_summary,
                       fact_timeframe, confidence_score, importance_score
                FROM user_facts
                WHERE user_id = %s AND category = %s AND status = 'active'
                ORDER BY importance_score DESC, last_referenced DESC
                LIMIT %s
                """
                cursor.execute(query, (user_id, category, limit))
            else:
                query = """
                SELECT fact_id, fact_type, category, fact_text, fact_summary,
                       fact_timeframe, confidence_score, importance_score
                FROM user_facts
                WHERE user_id = %s AND status = 'active'
                ORDER BY importance_score DESC, last_referenced DESC
                LIMIT %s
                """
                cursor.execute(query, (user_id, limit))

            facts = cursor.fetchall()
            return [dict(fact) for fact in facts]

        finally:
            cursor.close()
            self._put_conn(conn)

    # ==================================================================
    # CACHE PERFORMANCE TRACKING
    # ==================================================================

    def log_cache_performance(self, user_id: int, session_id: str,
                             total_tokens: int, cached_tokens: int):
        """Log OpenAI cache performance metrics"""
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            cache_hit_rate = (cached_tokens / total_tokens * 100) if total_tokens > 0 else 0

            # Calculate cost saved (GPT-4o-mini: $0.15/1M input, 50% discount on cached)
            cost_per_token = 0.15 / 1_000_000
            cost_saved = cached_tokens * cost_per_token * 0.5

            query = """
            INSERT INTO cache_performance (
                user_id, session_id, total_input_tokens, cached_tokens,
                cache_hit_rate, cost_saved
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                user_id, session_id, total_tokens, cached_tokens,
                cache_hit_rate, cost_saved
            ))

            conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error("Error logging cache performance: {e}")
        finally:
            cursor.close()
            self._put_conn(conn)

    def close(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("PostgreSQL connections closed")
