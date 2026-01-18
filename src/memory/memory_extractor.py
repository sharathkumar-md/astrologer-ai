"""
MemoryExtractor - Automatic fact extraction from conversations

NOTE: Database removed - this module is now a no-op stub.
Fact extraction and storage is handled externally by AstroVoice integration.
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

    NOTE: Database removed - extraction returns facts but doesn't store them.
    Storage is handled externally by AstroVoice integration.
    """

    def __init__(self, openai_client=None):
        """
        Initialize memory extractor

        Args:
            openai_client: OpenAI client (optional)
        """
        self.client = openai_client or OpenAI(api_key=config.OPENAI_API_KEY)

    def extract_facts_from_conversation(self, user_id: int,
                                       conversation_messages: List[Dict],
                                       session_id: str = None) -> List[Dict]:
        """
        Extract facts from a conversation (no storage - returns facts only)

        Args:
            user_id: User ID
            conversation_messages: List of messages [{"role": "user", "content": "..."}]
            session_id: Session ID (optional)

        Returns:
            List of extracted facts (not stored)
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

            logger.info(f"Extracted {len(facts)} facts from {len(conversation_messages)} messages (not stored - DB removed)")

            return facts

        except Exception as e:
            logger.info(f"Extraction failed: {e}")
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

    def extract_facts_from_session(self, user_id: int, session_id: str,
                                   min_messages: int = 4) -> List[Dict]:
        """
        Extract facts from a complete session (no-op without DB)

        Args:
            user_id: User ID
            session_id: Session ID to analyze
            min_messages: Minimum messages before extraction (default: 4)

        Returns:
            Empty list (DB removed - no session history available)
        """
        logger.info(f"extract_facts_from_session called but DB removed - returning empty")
        return []

    def should_extract(self, message_count: int, last_extraction_count: int = 0) -> bool:
        """
        Determine if we should extract facts

        Args:
            message_count: Current message count in session
            last_extraction_count: Message count at last extraction

        Returns:
            False (extraction disabled without DB)
        """
        # Extraction disabled without database storage
        return False


# Convenience function
def extract_facts(user_id: int, conversation_messages: List[Dict]) -> List[Dict]:
    """
    Quick fact extraction (convenience function)

    Args:
        user_id: User ID
        conversation_messages: Conversation messages

    Returns:
        List of extracted facts (not stored)
    """
    extractor = MemoryExtractor()
    return extractor.extract_facts_from_conversation(user_id, conversation_messages)
