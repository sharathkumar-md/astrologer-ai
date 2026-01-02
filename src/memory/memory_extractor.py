"""
MemoryExtractor - Automatic fact extraction from conversations
Extracts important information and stores in user_facts table
"""

from openai import OpenAI
from src.utils import config
from typing import List, Dict
import json
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)



class MemoryExtractor:
    """
    Extract important facts from conversations using LLM
    Stores in user_facts table for long-term memory
    """

    def __init__(self, db, openai_client=None):
        """
        Initialize memory extractor

        Args:
            db: Database instance (PostgreSQL or SQLite)
            openai_client: OpenAI client (optional)
        """
        self.db = db
        self.client = openai_client or OpenAI(api_key=config.OPENAI_API_KEY)

    def extract_facts_from_conversation(self, user_id: int,
                                       conversation_messages: List[Dict],
                                       session_id: str = None) -> List[Dict]:
        """
        Extract facts from a conversation

        Args:
            user_id: User ID
            conversation_messages: List of messages [{"role": "user", "content": "..."}]
            session_id: Session ID (optional)

        Returns:
            List of extracted facts
        """

        if len(conversation_messages) < 2:
            # Need at least one exchange to extract facts
            return []

        # Format conversation for analysis
        conversation_text = self._format_conversation(conversation_messages)

        # Extract facts using LLM
        extraction_prompt = f"""Analyze this astrology consultation conversation and extract IMPORTANT, CONCRETE facts about the user.

CONVERSATION:
{conversation_text}

Extract facts that are:
1. Specific and concrete (not vague)
2. Relevant for future consultations
3. Long-term or ongoing (not temporary)

For each fact, provide:
- fact_type: "career", "relationship", "health", "personal", "financial", "family"
- category: "current_situation", "goals", "challenges", "achievements", "life_events"
- fact_text: The complete fact in one sentence
- fact_summary: Short version (5-10 words)
- timeframe: "current", "past", "future_goal", "ongoing"
- confidence: 0.0 to 1.0 (how confident are you?)
- importance: 0.0 to 1.0 (how important is this fact?)

Return as JSON array. Example:
[
  {{
    "fact_type": "career",
    "category": "current_situation",
    "fact_text": "User is a software engineer with 3 years experience, currently working at a startup",
    "fact_summary": "Software engineer, 3 yrs, startup",
    "timeframe": "current",
    "confidence": 0.95,
    "importance": 0.85
  }}
]

IMPORTANT: Only extract 3-5 MOST IMPORTANT facts. Quality over quantity.
Return ONLY the JSON array, no other text."""

        try:
            # Call LLM for extraction
            response = self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,  # Lower temp for consistent extraction
                max_tokens=800
            )

            # Parse response
            response_text = response.choices[0].message.content.strip()

            # Extract JSON from response
            facts = self._parse_json_response(response_text)

            if not facts:
                logger.info("No facts extracted")
                return []

            # Store facts in database
            stored_facts = []
            for fact in facts:
                try:
                    fact_id = self._store_fact(user_id, fact, session_id)
                    fact['fact_id'] = fact_id
                    stored_facts.append(fact)
                    logger.info("Stored fact: {fact['fact_summary']}")
                except Exception as e:
                    logger.info("Error storing fact: {e}")

            # Log consolidation
            self._log_consolidation(
                user_id=user_id,
                session_id=session_id,
                message_count=len(conversation_messages),
                facts_extracted=len(stored_facts),
                tokens_used=response.usage.total_tokens
            )

            logger.info("Extracted {len(stored_facts)} facts from {len(conversation_messages)} messages")

            return stored_facts

        except Exception as e:
            logger.info("Extraction failed: {e}")
            return []

    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation messages for extraction"""
        lines = []
        for msg in messages:
            role = "User" if msg.get("role") == "user" else "Astra"
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _parse_json_response(self, response_text: str) -> List[Dict]:
        """Parse JSON from LLM response"""
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except:
            # Try to find JSON array in text
            start = response_text.find('[')
            end = response_text.rfind(']') + 1

            if start >= 0 and end > start:
                json_text = response_text[start:end]
                try:
                    return json.loads(json_text)
                except:
                    pass

            return []

    def _store_fact(self, user_id: int, fact: Dict, session_id: str = None) -> int:
        """Store fact in database"""

        # Check if database has add_user_fact method (PostgreSQL)
        if hasattr(self.db, 'add_user_fact'):
            fact_id = self.db.add_user_fact(
                user_id=user_id,
                fact_type=fact.get('fact_type', 'general'),
                category=fact.get('category', 'other'),
                fact_text=fact.get('fact_text', ''),
                fact_summary=fact.get('fact_summary', ''),
                fact_timeframe=fact.get('timeframe', 'current'),
                confidence=fact.get('confidence', 0.7),
                importance=fact.get('importance', 0.7)
            )
            return fact_id
        else:
            # SQLite doesn't have facts table
            logger.info("Warning: Database doesn't support facts storage")
            return 0

    def _log_consolidation(self, user_id: int, session_id: str,
                          message_count: int, facts_extracted: int,
                          tokens_used: int):
        """Log memory consolidation event"""

        # Only log if using PostgreSQL with proper table
        if not hasattr(self.db, '_get_conn'):
            return

        try:
            conn = self.db._get_conn()
            cursor = conn.cursor()

            query = """
            INSERT INTO memory_consolidation_log (
                user_id, session_id, consolidation_type,
                input_message_count, facts_extracted, summary_generated,
                llm_model_used, tokens_used, processing_time_ms, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                user_id,
                session_id,
                'fact_extraction',
                message_count,
                facts_extracted,
                False,  # summary_generated
                config.MODEL_NAME,
                tokens_used,
                0,  # processing_time_ms (not tracking for now)
                'success'
            ))

            conn.commit()
            cursor.close()
            self.db._put_conn(conn)

        except Exception as e:
            logger.info("Error logging consolidation: {e}")

    def extract_facts_from_session(self, user_id: int, session_id: str,
                                   min_messages: int = 4) -> List[Dict]:
        """
        Extract facts from a complete session

        Args:
            user_id: User ID
            session_id: Session ID to analyze
            min_messages: Minimum messages before extraction (default: 4)

        Returns:
            List of extracted facts
        """

        # Get all messages from this session
        if hasattr(self.db, '_get_conn'):
            # PostgreSQL
            conn = self.db._get_conn()
            cursor = conn.cursor()

            query = """
            SELECT role, content
            FROM conversations
            WHERE user_id = %s AND session_id = %s
            ORDER BY timestamp ASC
            """

            cursor.execute(query, (user_id, session_id))
            rows = cursor.fetchall()
            cursor.close()
            self.db._put_conn(conn)

            messages = [{"role": row[0], "content": row[1]} for row in rows]

        else:
            # SQLite fallback
            messages = self.db.get_conversation_history(user_id, limit=50)

        if len(messages) < min_messages:
            logger.info("Not enough messages ({len(messages)} < {min_messages})")
            return []

        return self.extract_facts_from_conversation(user_id, messages, session_id)

    def should_extract(self, message_count: int, last_extraction_count: int = 0) -> bool:
        """
        Determine if we should extract facts

        Args:
            message_count: Current message count in session
            last_extraction_count: Message count at last extraction

        Returns:
            True if should extract
        """

        # Extract after every 5-6 messages
        messages_since_last = message_count - last_extraction_count

        return messages_since_last >= 5


# Convenience function
def extract_facts(db, user_id: int, conversation_messages: List[Dict]) -> List[Dict]:
    """
    Quick fact extraction (convenience function)

    Args:
        db: Database instance
        user_id: User ID
        conversation_messages: Conversation messages

    Returns:
        List of extracted facts
    """
    extractor = MemoryExtractor(db)
    return extractor.extract_facts_from_conversation(user_id, conversation_messages)
