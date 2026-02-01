"""
CachedContextBuilder - OpenAI Prompt Caching Optimized Context Builder
Builds LLM context optimized for maximum cache hit rates

NOTE: Database removed - conversation history is passed directly.
Data will be provided by AstroVoice integration.
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

    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        Initialize context builder

        Args:
            openai_client: OpenAI client instance (optional)
        """
        self.client = openai_client or OpenAI(api_key=config.OPENAI_API_KEY)

    def build_messages(self, user_id: int, current_query: str,
                      natal_context: str, transit_context: str = "",
                      system_prompt: str = None, session_id: str = None,
                      character_id: str = "general",
                      conversation_history: List[Dict] = None,
                       character_data: dict = None) -> List[Dict]:
        """
        Build messages array optimized for OpenAI caching

        Args:
            user_id: User ID
            current_query: Current user query
            natal_context: Birth chart context
            transit_context: Current transits context (optional)
            system_prompt: Custom system prompt (optional)
            session_id: Session ID (for logging only, not DB lookup)
            character_id: Character persona ID (general, career, love, health, finance, family, spiritual)
            conversation_history: Conversation history passed from caller (no DB lookup)

        Returns:
            List of message dictionaries for OpenAI API
        """

        messages = []

        # 1. SYSTEM PROMPT (Static - always cached after first call)
        # Use character-specific prompt if not provided
        if not system_prompt:
            from src.utils.characters import get_character_prompt
            system_prompt = get_character_prompt(character_data)

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

        # 3. USER FACTS - No longer stored in DB, skip this section
        # Facts can be passed via conversation_history if needed

        # 4. RECENT CONVERSATION (from passed conversation_history)
        # REDUCED LIMIT: Keep only last 10 messages to prevent astro context from being pushed out
        recent_messages = self._get_recent_messages(conversation_history, limit=10)
        messages.extend(recent_messages)

        # 4.5 FORMAT REMINDER (Always added before current query)
        # This ensures the model follows format and uses astrology
        messages.append({
            "role": "system",
            "content": "REMINDER: Reply in 1-3 SHORT messages (8-20 words each) separated by |||. Use BIRTH CHART data. Example: 'Hmm achha|||Teri kundali mein 10th house strong hai|||Iss phase mein career grow hoga'"
        })

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

    def _get_recent_messages(self, conversation_history: List[Dict] = None, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation messages from passed history

        Args:
            conversation_history: Conversation history passed from caller
            limit: Maximum messages to retrieve (default: 10 to prevent context overflow)

        Returns:
            List of conversation messages
        """
        if not conversation_history:
            return []

        # Return last N messages
        return conversation_history[-limit:] if len(conversation_history) > limit else conversation_history

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
        """Log cache performance (no-op without database)"""
        # Database removed - just log to console for debugging
        logger.debug(f"Cache stats for user {user_id}: {cache_stats.get('cache_hit_rate', 0):.1f}% hit rate")


# Convenience function for backward compatibility
def build_context_with_caching(user_id: int, current_query: str,
                               natal_context: str, transit_context: str = "",
                               conversation_history: List[Dict] = None) -> List[Dict]:
    """
    Build context with caching optimization (convenience function)

    Args:
        user_id: User ID
        current_query: Current user query
        natal_context: Birth chart context
        transit_context: Transits context (optional)
        conversation_history: Conversation history (optional)

    Returns:
        List of messages optimized for OpenAI caching
    """

    builder = CachedContextBuilder()
    return builder.build_messages(
        user_id=user_id,
        current_query=current_query,
        natal_context=natal_context,
        transit_context=transit_context,
        conversation_history=conversation_history
    )
