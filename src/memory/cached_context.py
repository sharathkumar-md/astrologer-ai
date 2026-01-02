"""
CachedContextBuilder - OpenAI Prompt Caching Optimized Context Builder
Builds LLM context optimized for maximum cache hit rates
"""

from openai import OpenAI
from typing import List, Dict, Optional
from src.utils import config

from src.utils.logger import setup_logger

logger = setup_logger(__name__)



class CachedContextBuilder:
    """
    Build LLM context optimized for OpenAI prompt caching

    Structures messages in order of stability:
    1. System prompt (STATIC - cached longest)
    2. Birth chart (STATIC - cached longest)
    3. User facts (SEMI-STATIC - updates occasionally)
    4. Recent conversation (GROWING - prefix cached)
    5. Current query (NEW - never cached)
    """

    def __init__(self, db, openai_client: Optional[OpenAI] = None):
        """
        Initialize context builder

        Args:
            db: Database instance (PostgreSQL or SQLite)
            openai_client: OpenAI client instance (optional)
        """
        self.db = db
        self.client = openai_client or OpenAI(api_key=config.OPENAI_API_KEY)

    def build_messages(self, user_id: int, current_query: str,
                      natal_context: str, transit_context: str = "",
                      system_prompt: str = None) -> List[Dict]:
        """
        Build messages array optimized for OpenAI caching

        Args:
            user_id: User ID
            current_query: Current user query
            natal_context: Birth chart context
            transit_context: Current transits context (optional)
            system_prompt: Custom system prompt (optional)

        Returns:
            List of message dictionaries for OpenAI API
        """

        messages = []

        # 1. SYSTEM PROMPT (Static - always cached after first call)
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()

        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # 2. BIRTH CHART CONTEXT (Static - always cached)
        chart_content = f"=== BIRTH CHART ===\n{natal_context}"

        if transit_context:
            chart_content += f"\n\n=== CURRENT TRANSITS ===\n{transit_context}"

        messages.append({
            "role": "system",
            "content": chart_content
        })

        # 3. USER FACTS (Semi-static - cached until facts change)
        user_facts = self._get_user_facts(user_id)
        if user_facts:
            facts_content = self._format_user_facts(user_facts)
            messages.append({
                "role": "system",
                "content": f"=== KNOWN FACTS ABOUT USER (Long-term Memory) ===\n{facts_content}"
            })

        # 4. RECENT CONVERSATION (Growing - prefix cached)
        recent_messages = self._get_recent_messages(user_id, limit=20)
        messages.extend(recent_messages)

        # 5. CURRENT QUERY (New - not cached)
        messages.append({
            "role": "user",
            "content": current_query
        })

        return messages

    def _get_default_system_prompt(self) -> str:
        """Get default ASTRA system prompt"""
        return """You are Astra — a warm, empathetic Vedic astrology consultant. You adapt your language to match the user's language EXACTLY.

CRITICAL RULES:
1. LANGUAGE ADAPTATION:
   - ALWAYS reply in the SAME language the user is using
   - Supported Indian languages: Hindi, Hinglish, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, Urdu
   - If user speaks in Telugu, reply ONLY in Telugu (romanized)
   - If user speaks in Tamil, reply ONLY in Tamil (romanized)
   - If user speaks in Hindi/Hinglish, reply in Hinglish
   - If user speaks in English, reply in English
   - Match the user's language style and tone exactly
   - DO NOT mix languages - if they speak Telugu, don't reply in Hindi!

2. CORRECT LANGUAGE USAGE:
   - For Hinglish: Use "Aapko" instead of "Aapki" for "you" (Aapko kya chahiye?, not Aapki kya chahiye?)
   - For Hinglish: Use "Mujhe" for "me" (Mujhe nahi pata, not Main nahi pata)
   - For Telugu: Use proper Telugu romanization (naaku, meeru, emi, ela, etc.)
   - For Tamil: Use proper Tamil romanization (naan, nee, enna, eppadi, etc.)
   - Keep grammar natural and conversational in the target language

3. CONTEXT AWARENESS:
   - REMEMBER the user's previous messages from conversation history
   - REMEMBER important facts about the user from long-term memory
   - If user answers your question, GIVE ASTROLOGICAL INSIGHTS immediately
   - Don't ask the same question again
   - Maintain conversation flow naturally
   - Reference past discussions when relevant

4. QUESTION GUIDELINES:
   - Ask ONLY practical, non-technical questions
   - NO astrological jargon in questions
   - Questions should be about their situation, not planets/transits
   - Ask 1-2 questions MAX, then wait for answer

5. RESPONSE FORMAT:
   - 1-3 short chat messages
   - Separate with "|||"
   - Each message: 8-20 words maximum
   - Sound natural and human

REMEMBER: Be a helpful astrology consultant who remembers the conversation and speaks the user's language!"""

    def _get_user_facts(self, user_id: int) -> List[Dict]:
        """Get important facts about user from database"""

        # Check if database has get_user_facts method (PostgreSQL)
        if hasattr(self.db, 'get_user_facts'):
            try:
                return self.db.get_user_facts(user_id, limit=15)
            except:
                return []

        # Fallback for SQLite (no facts table yet)
        return []

    def _format_user_facts(self, facts: List[Dict]) -> str:
        """Format facts for system message"""

        if not facts:
            return ""

        # Group by category
        by_category = {}
        for fact in facts:
            cat = fact.get('category', 'general')
            if cat not in by_category:
                by_category[cat] = []

            fact_text = fact.get('fact_text', '')
            importance = fact.get('importance_score', 0.5)

            # Add importance stars
            stars = "⭐" * int(importance * 5) if importance > 0.5 else ""

            by_category[cat].append({
                'text': fact_text,
                'stars': stars
            })

        # Format
        lines = []
        for category, fact_list in by_category.items():
            lines.append(f"\n{category.upper()}:")
            for fact in fact_list:
                stars = f" {fact['stars']}" if fact['stars'] else ""
                lines.append(f"  • {fact['text']}{stars}")

        return "\n".join(lines)

    def _get_recent_messages(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent conversation messages"""

        try:
            history = self.db.get_conversation_history(user_id, limit=limit)
            return history
        except Exception as e:
            logger.warning("Error getting conversation history: {e}")
            return []

    def get_cache_stats(self, usage_obj) -> Dict:
        """
        Extract cache statistics from OpenAI response usage object

        Args:
            usage_obj: OpenAI response.usage object

        Returns:
            Dictionary with cache statistics
        """

        total_input = usage_obj.prompt_tokens

        # Access cached tokens from prompt_tokens_details
        # This is a Pydantic object, not a dict
        try:
            prompt_details = getattr(usage_obj, 'prompt_tokens_details', None)
            if prompt_details and hasattr(prompt_details, 'cached_tokens'):
                cached_tokens = prompt_details.cached_tokens or 0
            else:
                cached_tokens = 0
        except:
            cached_tokens = 0

        cache_hit_rate = (cached_tokens / total_input * 100) if total_input > 0 else 0

        # Calculate cost saved (GPT-4.1-mini pricing similar to GPT-4o-mini)
        cost_per_token = 0.15 / 1_000_000  # $0.15 per 1M tokens
        cost_saved = cached_tokens * cost_per_token * 0.5  # 50% discount

        return {
            'total_input_tokens': total_input,
            'cached_tokens': cached_tokens,
            'cache_hit_rate': cache_hit_rate,
            'cost_saved_usd': cost_saved,
            'output_tokens': usage_obj.completion_tokens
        }

    def log_cache_performance(self, user_id: int, session_id: str, cache_stats: Dict):
        """Log cache performance to database"""

        # Only log if using PostgreSQL with cache_performance table
        if hasattr(self.db, 'log_cache_performance'):
            try:
                self.db.log_cache_performance(
                    user_id=user_id,
                    session_id=session_id,
                    total_tokens=cache_stats['total_input_tokens'],
                    cached_tokens=cache_stats['cached_tokens']
                )
            except Exception as e:
                logger.warning("Error logging cache performance: {e}")


# Convenience function for backward compatibility
def build_context_with_caching(db, user_id: int, current_query: str,
                               natal_context: str, transit_context: str = "") -> List[Dict]:
    """
    Build context with caching optimization (convenience function)

    Args:
        db: Database instance
        user_id: User ID
        current_query: Current user query
        natal_context: Birth chart context
        transit_context: Transits context (optional)

    Returns:
        List of messages optimized for OpenAI caching
    """

    builder = CachedContextBuilder(db)
    return builder.build_messages(
        user_id=user_id,
        current_query=current_query,
        natal_context=natal_context,
        transit_context=transit_context
    )
