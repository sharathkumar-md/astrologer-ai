"""
Consolidated LLM Bridge for ASTRA
Combines sophisticated conversation management with OpenAI prompt caching
"""

from openai import OpenAI
import re
from typing import List, Dict, Optional
from src.utils import config
from src.utils.logger import setup_logger
from src.utils.identity_guard import IdentityGuard
from src.memory.cached_context import CachedContextBuilder
from src.database.db_adapter import get_db_instance

logger = setup_logger(__name__)


# ASTRA System Prompt
ASTRA_SYSTEM_PROMPT = """You are Astra — a warm, empathetic Vedic astrology consultant. You adapt your language to match the user's language EXACTLY.

CRITICAL RULES:

0. IDENTITY (MOST IMPORTANT):
   - You ARE Astra, a Vedic astrology consultant
   - NEVER mention or acknowledge being an AI, LLM, language model, ChatGPT, GPT, or any AI system
   - NEVER discuss your training, model, or technical implementation
   - If asked about your identity, simply state: "I am Astra, your Vedic astrology guide"
   - Focus on astrology, cosmic guidance, and helping users
   - Stay in character as a knowledgeable astrologer at all times

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
   - REMEMBER the user's previous messages
   - If user answers your question, GIVE ASTROLOGICAL INSIGHTS immediately
   - Don't ask the same question again
   - Maintain conversation flow naturally

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

EXAMPLE CONVERSATIONS:

HINGLISH:
User: "Meri job ki problem hai"
You: "Kis field mein kaam karte ho?|||Kitne time se problem hai?"

TELUGU:
User: "Naaku naa udyogam gurinchi matladali"
You: "Meeru e field lo pani chestunnaru?|||Inta time nundi problem undi?"

TAMIL:
User: "Enakku vela pathi pesanum"
You: "Neenga enna field la vela seiyareengal?|||Evvalavu naal problem irukku?"

REMEMBER: Be a helpful astrology consultant who remembers the conversation and speaks the user's language!"""


class LLMBridge:
    """
    Unified LLM Bridge with:
    - Sophisticated conversation state management (from original LLMBridge)
    - Language detection and adaptation
    - Intent analysis
    - OpenAI prompt caching optimization (from EnhancedLLMBridge)
    - Automatic fact extraction integration
    """

    def __init__(self, db=None, use_caching=True, use_identity_guard=True):
        """
        Initialize LLM bridge

        Args:
            db: Database instance (optional, will create if not provided)
            use_caching: Whether to use prompt caching (default: True)
            use_identity_guard: Whether to use identity guard (default: True)
        """
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.MODEL_NAME
        self.db = db or get_db_instance()
        self.use_caching = use_caching

        if self.use_caching:
            self.context_builder = CachedContextBuilder(self.db, self.client)
            logger.info("LLMBridge initialized with caching enabled")
        else:
            logger.info("LLMBridge initialized without caching")

        # Initialize identity guard
        self.identity_guard = None
        if use_identity_guard:
            try:
                self.identity_guard = IdentityGuard(threshold=0.80)
                logger.info("Identity Guard initialized (threshold: 0.80)")
            except Exception as e:
                logger.error(f"Failed to initialize Identity Guard: {e}")

        # Load system prompt from file
        self.system_prompt = ASTRA_SYSTEM_PROMPT

        # Conversation state management (from original)
        self.conversation_state = {
            "current_topic": None,
            "has_asked_questions": False,
            "user_details": {},
            "conversation_stage": "initial",
            "previous_topics": [],
            "language_preference": "hinglish",
            "last_question_asked": None,
            "waiting_for_answer": False,
            "topic_context": {}
        }

    def generate_response(self, user_id: int = None, user_query: str = None,
                         natal_context: str = None, transit_context: str = "",
                         session_id: str = None, conversation_history: list = None):
        """
        Generate response with optional caching

        Supports both caching mode (with user_id) and original mode (without user_id)

        Args:
            user_id: User ID (optional, enables caching if provided)
            user_query: User's current query
            natal_context: Birth chart context
            transit_context: Current transits context
            session_id: Session ID
            conversation_history: Conversation history (for non-caching mode)

        Returns:
            Dictionary with response and cache stats OR just response string
        """
        # IDENTITY GUARD: Intercept identity-related queries
        if self.identity_guard and user_query:
            language = self.conversation_state.get("language_preference", "hinglish")
            intercepted_response = self.identity_guard.intercept_if_needed(user_query, language)

            if intercepted_response:
                # Return identity response in consistent format
                return {
                    'response': intercepted_response,
                    'cache_stats': {
                        'total_input_tokens': 0,
                        'cached_tokens': 0,
                        'cache_hit_rate': 0,
                        'cost_saved_usd': 0
                    },
                    'intercepted': True  # Flag to indicate this was intercepted
                }

        # If caching enabled and we have user_id, use cached generation
        if self.use_caching and user_id is not None:
            result = self._generate_with_caching(
                user_id=user_id,
                user_query=user_query,
                natal_context=natal_context,
                transit_context=transit_context,
                session_id=session_id
            )
            return result
        else:
            # Use original generation method
            response = self._generate_original(
                natal_context=natal_context,
                transit_context=transit_context,
                user_query=user_query,
                conversation_history=conversation_history or []
            )

            # Return dict format for consistency
            if isinstance(response, str):
                return {
                    'response': response,
                    'cache_stats': {
                        'total_input_tokens': 0,
                        'cached_tokens': 0,
                        'cache_hit_rate': 0,
                        'cost_saved_usd': 0
                    }
                }
            return response

    def _generate_with_caching(self, user_id: int, user_query: str,
                               natal_context: str, transit_context: str,
                               session_id: str = None) -> dict:
        """Generate response using cached context (from EnhancedLLMBridge)"""

        from datetime import datetime

        if not session_id:
            session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # Build messages optimized for caching
            messages = self.context_builder.build_messages(
                user_id=user_id,
                current_query=user_query,
                natal_context=natal_context,
                transit_context=transit_context
            )

            # Call OpenAI
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=160,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.2
            )

            response_text = completion.choices[0].message.content.strip()
            cache_stats = self.context_builder.get_cache_stats(completion.usage)

            # Log cache performance
            self.context_builder.log_cache_performance(
                user_id=user_id,
                session_id=session_id,
                cache_stats=cache_stats
            )

            # Store conversation
            self.db.add_conversation(
                user_id=user_id,
                query=user_query,
                response=response_text,
                session_id=session_id
            )

            hit_rate = cache_stats['cache_hit_rate']
            cached = cache_stats['cached_tokens']
            total = cache_stats['total_input_tokens']

            logger.info(f"Cache: {cached}/{total} tokens ({hit_rate:.1f}%) | Saved: ${cache_stats['cost_saved_usd']:.6f}")

            return {
                'response': response_text,
                'cache_stats': cache_stats,
                'session_id': session_id
            }

        except Exception as e:
            logger.error(f"LLM generation with caching failed: {e}")
            raise


    def _detect_language(self, text):
        """Detect if text is English, Hindi/Hinglish, Telugu, Tamil, or other Indian languages"""
        text_lower = text.lower()
        
        # Check for Telugu script (Unicode range: 0C00-0C7F)
        telugu_pattern = r'[\u0C00-\u0C7F]'
        if re.search(telugu_pattern, text):
            return "telugu"
        
        # Check for Tamil script (Unicode range: 0B80-0BFF)
        tamil_pattern = r'[\u0B80-\u0BFF]'
        if re.search(tamil_pattern, text):
            return "tamil"
        
        # Check for Kannada script (Unicode range: 0C80-0CFF)
        kannada_pattern = r'[\u0C80-\u0CFF]'
        if re.search(kannada_pattern, text):
            return "kannada"
        
        # Check for Malayalam script (Unicode range: 0D00-0D7F)
        malayalam_pattern = r'[\u0D00-\u0D7F]'
        if re.search(malayalam_pattern, text):
            return "malayalam"
        
        # Check for Bengali script (Unicode range: 0980-09FF)
        bengali_pattern = r'[\u0980-\u09FF]'
        if re.search(bengali_pattern, text):
            return "bengali"
        
        # Check for Gujarati script (Unicode range: 0A80-0AFF)
        gujarati_pattern = r'[\u0A80-\u0AFF]'
        if re.search(gujarati_pattern, text):
            return "gujarati"
        
        # Check for Punjabi/Gurmukhi script (Unicode range: 0A00-0A7F)
        punjabi_pattern = r'[\u0A00-\u0A7F]'
        if re.search(punjabi_pattern, text):
            return "punjabi"
        
        # Common Telugu romanized words
        telugu_indicators = [
            'naaku', 'naa', 'nenu', 'meeru', 'mee', 'emi', 'ela', 'ekkada', 'eppudu',
            'enduku', 'gurinchi', 'tho', 'lo', 'ki', 'ku', 'ni', 'nu', 'chala',
            'bagundi', 'ledu', 'undi', 'unnadi', 'chesanu', 'chestanu', 'udyogam',
            'pani', 'intlo', 'bayata', 'roju', 'nelalu', 'samvatsaralu', 'matladali',
            'vastundi', 'vastanu', 'cheppandi', 'kavali', 'kavalenu'
        ]
        
        # Common Tamil romanized words
        tamil_indicators = [
            'naan', 'nee', 'enna', 'eppadi', 'enga', 'eppo', 'yean',
            'ungal', 'enakku', 'unakku', 'romba', 'nalla', 'illa',
            'irukku', 'pannanum', 'vela', 'veedu', 'pesanum', 'pathi',
            'seiyareengal', 'theriyum', 'purinjuthu', 'varum', 'poren',
            'sollunga', 'venum', 'vendam', 'mudiyum', 'mudiyathu'
        ]
        
        # Common Kannada romanized words
        kannada_indicators = [
            'naanu', 'neevu', 'yenu', 'hege', 'elli', 'yaavaga', 'yaake',
            'nanna', 'nimma', 'ide', 'illa', 'beku', 'beda', 'maadi',
            'kelasa', 'mane', 'tumba', 'chennagi', 'gottu', 'gottilla',
            'barthini', 'hogthini', 'heli', 'kodi', 'tagondu'
        ]
        
        # Common Malayalam romanized words
        malayalam_indicators = [
            'njan', 'nee', 'ningal', 'enthu', 'engane', 'evide', 'eppol', 'enthinu',
            'ente', 'ningalude', 'undu', 'illa', 'venam', 'venda', 'cheyyuka',
            'pani', 'veedu', 'valare', 'nannaayi', 'ariyam', 'ariyilla',
            'varum', 'pokum', 'parayuka', 'tharika', 'edukkuka'
        ]
        
        # Common Bengali romanized words
        bengali_indicators = [
            'ami', 'tumi', 'apni', 'ki', 'kivabe', 'kothay', 'kakhon', 'keno',
            'amar', 'tomar', 'apnar', 'ache', 'nei', 'chai', 'chaina',
            'korbo', 'korte', 'kaj', 'bari', 'khub', 'bhalo', 'jani', 'janina',
            'asbo', 'jabo', 'bolo', 'dao', 'nao'
        ]
        
        # Common Gujarati romanized words
        gujarati_indicators = [
            'hun', 'tame', 'shu', 'kevi', 'kya', 'kyare', 'shu mate', 'karu',
            'maru', 'tamaru', 'che', 'nathi', 'joiye', 'nai joiye',
            'kam', 'ghar', 'khub', 'saru', 'jaanu', 'nathi jaanu',
            'aavish', 'javanu', 'kaho', 'apo', 'lo'
        ]
        
        # Common Punjabi romanized words
        punjabi_indicators = [
            'main', 'tu', 'tusi', 'ki', 'kiven', 'kithe', 'kado', 'kyu',
            'mera', 'tera', 'tuhada', 'hai', 'nahi', 'chahida', 'nahi chahida',
            'karna', 'kam', 'ghar', 'bahut', 'changa', 'pata', 'pata nahi',
            'aavanga', 'jaana', 'dasso', 'deo', 'lao'
        ]
        
        # Common Marathi romanized words
        marathi_indicators = [
            'mi', 'tu', 'tumhi', 'kay', 'kasa', 'kuthe', 'kevha', 'ka',
            'maza', 'tuza', 'tumcha', 'aahe', 'nahi', 'pahije', 'nako',
            'karnya', 'kam', 'ghar', 'khup', 'changle', 'mahit', 'mahit nahi',
            'yeil', 'janar', 'sang', 'de', 'ghe'
        ]
        
        # Common Hindi/Hinglish words and patterns
        hindi_indicators = [
            'hai', 'ho', 'hain', 'ka', 'ki', 'ke', 'ko', 'se', 'mein', 'par',
            'nahi', 'nhi', 'kyun', 'kya', 'kaise', 'kab', 'kahan', 'kitna',
            'mujhe', 'tumhe', 'aapko', 'mera', 'tera', 'hamara', 'apna',
            'accha', 'theek', 'thik', 'acha', 'bahut', 'zyada', 'kam',
            'dhanyawad', 'shukriya', 'namaste', 'pranam', 'mahine', 'saal'
        ]
        
        # Count language indicators
        telugu_score = sum(1 for word in telugu_indicators if word in text_lower)
        tamil_score = sum(1 for word in tamil_indicators if word in text_lower)
        kannada_score = sum(1 for word in kannada_indicators if word in text_lower)
        malayalam_score = sum(1 for word in malayalam_indicators if word in text_lower)
        bengali_score = sum(1 for word in bengali_indicators if word in text_lower)
        gujarati_score = sum(1 for word in gujarati_indicators if word in text_lower)
        punjabi_score = sum(1 for word in punjabi_indicators if word in text_lower)
        marathi_score = sum(1 for word in marathi_indicators if word in text_lower)
        hindi_score = sum(1 for word in hindi_indicators if word in text_lower)
        
        # Check for Devanagari characters (Hindi)
        devanagari_pattern = r'[\u0900-\u097F]'
        if re.search(devanagari_pattern, text):
            hindi_score += 5
        
        # Determine language based on scores
        # If both Telugu and Tamil have scores, check for specific unique words
        if telugu_score > 0 and tamil_score > 0:
            # Tamil-specific unique words
            tamil_unique = ['enakku', 'pesanum', 'pathi', 'nalla', 'romba', 'eppadi', 'ungal']
            # Telugu-specific unique words
            telugu_unique = ['naaku', 'matladali', 'gurinchi', 'meeru', 'bagundi', 'undi']
            
            tamil_unique_score = sum(1 for word in tamil_unique if word in text_lower)
            telugu_unique_score = sum(1 for word in telugu_unique if word in text_lower)
            
            if tamil_unique_score > telugu_unique_score:
                return "tamil"
            elif telugu_unique_score > tamil_unique_score:
                return "telugu"
        
        if telugu_score >= 2:
            return "telugu"
        elif tamil_score >= 2:
            return "tamil"
        elif hindi_score >= 2:
            return "hinglish"
        else:
            # Check if it's mostly English
            english_words = ['the', 'and', 'you', 'are', 'is', 'am', 'my', 'your', 'what', 'when', 'where', 'why', 'how']
            english_score = sum(1 for word in english_words if word in text_lower)
            
            if english_score > max(hindi_score, telugu_score, tamil_score):
                return "english"
            else:
                return "hinglish"
    

    def _is_answer_to_question(self, user_query, last_question):
        """Check if user is answering the previous question"""
        if not last_question:
            return False
        
        query_lower = user_query.lower()
        last_q_lower = last_question.lower()
        
        # Check if this looks like an answer (not a new question)
        is_new_question = any(word in query_lower for word in ['?', 'kya', 'kaise', 'kab', 'kyun', 'kahan', 'kitna', 'what', 'how', 'when', 'why', 'where'])
        
        # Check for time-related answers (common in astrology context)
        time_indicators = ['mahine', 'saal', 'week', 'month', 'year', 'din', 'time', 'lagbhag', 'around', 'about']
        has_time = any(indicator in query_lower for indicator in time_indicators)
        
        # Check for yes/no answers
        yes_no = ['haan', 'ha', 'yes', 'hmm', 'theek', 'ok', 'nhi', 'nahi', 'no', 'na']
        is_yes_no = query_lower.strip() in yes_no
        
        # Short answers are likely responses
        is_short_answer = len(query_lower.split()) <= 5 and not is_new_question
        
        # If it contains numbers with time units, it's likely an answer
        has_number_time = bool(re.search(r'\d+\s*(saal|mahine|din|week|month|year)', query_lower))
        
        return (is_short_answer and not is_new_question) or has_time or is_yes_no or has_number_time
    

    def _analyze_query_intent(self, user_query, conversation_history):
        """Deep analysis of what user really wants"""
        query = user_query.lower().strip()
        
        # Detect language for this query
        current_language = self._detect_language(user_query)
        
        # Update language preference based on current and history
        if conversation_history:
            # Check last few user messages for language pattern
            hindi_count = 0
            english_count = 0
            for msg in conversation_history[-4:]:
                if msg.get("role") == "user":
                    msg_lang = self._detect_language(msg.get("content", ""))
                    if msg_lang == "hinglish":
                        hindi_count += 1
                    else:
                        english_count += 1
            
            if hindi_count > english_count:
                self.conversation_state["language_preference"] = "hinglish"
            elif english_count > hindi_count:
                self.conversation_state["language_preference"] = "english"
        
        # 1. Check if this is an answer to our last question
        if self.conversation_state["waiting_for_answer"] and self.conversation_state["last_question_asked"]:
            if self._is_answer_to_question(user_query, self.conversation_state["last_question_asked"]):
                # User is answering our question - give insights now
                return {
                    "intent": "answer_received",
                    "urgency": "medium",
                    "needs_details": False,
                    "topic_details": {
                        "topic": self.conversation_state["current_topic"],
                        "subtopic": self.conversation_state.get("topic_context", {}).get("subtopic"),
                        "is_new_topic": False,
                        "needs_clarification": False,
                        "emotional_tone": self.conversation_state.get("topic_context", {}).get("emotional_tone", "neutral")
                    },
                    "language": current_language
                }
        
        # 2. Check for greetings
        is_simple_greeting = any(greeting in query for greeting in ['hi', 'hello', 'hey', 'namaste', 'namaskar'])
        is_how_are_you = any(phrase in query for phrase in ['kese ho', 'kaise ho', 'kese hain', 'kaise hain', 'how are you', 'how r u'])
        
        # Handle greetings
        if is_simple_greeting or is_how_are_you:
            if len(query.split()) <= 4:
                if not conversation_history or len(conversation_history) < 2:
                    return {
                        "intent": "greeting", 
                        "urgency": "low", 
                        "needs_details": False,
                        "greeting_type": "first",
                        "topic_details": {
                            "topic": "general",
                            "subtopic": None,
                            "is_new_topic": False,
                            "needs_clarification": False,
                            "emotional_tone": "neutral"
                        },
                        "language": current_language
                    }
                else:
                    return {
                        "intent": "greeting",
                        "urgency": "low", 
                        "needs_details": False,
                        "greeting_type": "return",
                        "topic_details": {
                            "topic": "general",
                            "subtopic": None,
                            "is_new_topic": False,
                            "needs_clarification": False,
                            "emotional_tone": "neutral"
                        },
                        "language": current_language
                    }
        
        # 3. Check for gratitude/ending
        if any(thank in query for thank in ['dhanyawad', 'dhanyavaad', 'thanks', 'thank you', 'shukriya', 'thanku']):
            return {
                "intent": "gratitude", 
                "urgency": "low", 
                "needs_details": False,
                "topic_details": {
                    "topic": "general",
                    "subtopic": None,
                    "is_new_topic": False,
                    "needs_clarification": False,
                    "emotional_tone": "grateful"
                },
                "language": current_language
            }
        
        # 4. Check for problem statements
        problem_indicators = [
            'problem', 'dikkat', 'mushkil', 'tension', 'pareshan', 'chinta',
            'worry', 'stress', 'nahi ho raha', 'nahi mil raha', 'fail',
            'kharab', 'bura', 'ladaai', 'fight', 'breakup', 'chhut', 'tod',
            'loss', 'harna', 'haar', 'gaya', 'gayi', 'gaye', 'samasya',
            'issue', 'difficulty', 'trouble', 'concern', 'anxious'
        ]
        
        is_problem = any(indicator in query for indicator in problem_indicators)
        
        # 5. Check for specific topics with context awareness
        topic_details = {
            "topic": "general",
            "subtopic": None,
            "is_new_topic": True,
            "needs_clarification": True,
            "emotional_tone": "neutral"
        }
        
        # Money/Financial context
        money_words = ['paisa', 'money', 'dhan', 'wealth', 'finance', 'loan', 'karza', 'udhar', 'investment', 'savings', 'income', 'financial', 'pesa']
        if any(word in query for word in money_words):
            topic_details["topic"] = "money"
            topic_details["emotional_tone"] = "worried" if is_problem else "hopeful"
            topic_details["subtopic"] = "income_issue"
        
        # Career/Job context
        career_words = ['job', 'career', 'naukri', 'kaam', 'business', 'work', 'office', 'promotion', 'salary', 'interview', 'company', 'boss']
        if any(word in query for word in career_words):
            topic_details["topic"] = "career"
            if 'nahi mil raha' in query or 'interview' in query:
                topic_details["subtopic"] = "job_search"
                topic_details["emotional_tone"] = "stressed"
            elif 'promotion' in query or 'badh' in query or 'growth' in query:
                topic_details["subtopic"] = "growth"
                topic_details["emotional_tone"] = "hopeful"
            elif 'business' in query:
                topic_details["subtopic"] = "business"
                topic_details["emotional_tone"] = "concerned"
            else:
                topic_details["emotional_tone"] = "stressed" if is_problem else "curious"
        
        # Legal/Law context
        legal_words = ['legal', 'case', 'court', 'judge', 'lawyer', 'judgment', 'decision', 'law', 'suit']
        if any(word in query for word in legal_words):
            topic_details["topic"] = "legal"
            topic_details["emotional_tone"] = "stressed"
            topic_details["subtopic"] = "legal_case"
        
        # Love/Relationship context
        love_words = ['love', 'pyaar', 'gf', 'bf', 'girlfriend', 'boyfriend', 'crush', 'shaadi', 'marriage', 'relationship', 'partner', 'wife', 'husband']
        if any(word in query for word in love_words):
            topic_details["topic"] = "love"
            if 'breakup' in query or 'chhut' in query or 'tod' in query or 'alag' in query:
                topic_details["subtopic"] = "breakup"
                topic_details["emotional_tone"] = "sad"
            elif 'ladaai' in query or 'fight' in query or 'jhagda' in query:
                topic_details["subtopic"] = "conflict"
                topic_details["emotional_tone"] = "upset"
            elif 'shaadi' in query or 'marriage' in query or 'vivah' in query:
                topic_details["subtopic"] = "marriage"
                topic_details["emotional_tone"] = "curious"
            elif 'milna' in query or 'mil jaye' in query or 'pata' in query:
                topic_details["subtopic"] = "meeting"
                topic_details["emotional_tone"] = "hopeful"
            else:
                topic_details["emotional_tone"] = "romantic" if not is_problem else "concerned"
        
        # Health context
        health_words = ['health', 'tabiyat', 'bimar', 'sick', 'ill', 'dard', 'pita', 'takleef', 'bimari', 'operation']
        if any(word in query for word in health_words):
            topic_details["topic"] = "health"
            topic_details["emotional_tone"] = "concerned"
            if 'mummy' in query or 'mother' in query or 'maa' in query:
                topic_details["subtopic"] = "mother_health"
            elif 'papa' in query or 'father' in query or 'baap' in query:
                topic_details["subtopic"] = "father_health"
            elif 'bhai' in query or 'behen' in query or 'sister' in query or 'brother' in query:
                topic_details["subtopic"] = "sibling_health"
            else:
                topic_details["subtopic"] = "personal_health"
        
        # Education context
        education_words = ['study', 'padhai', 'exam', 'college', 'university', 'result', 'marks', 'percentage', 'fail', 'pass', 'admission']
        if any(word in query for word in education_words):
            topic_details["topic"] = "education"
            topic_details["emotional_tone"] = "anxious" if is_problem else "hopeful"
            if 'exam' in query:
                topic_details["subtopic"] = "exams"
            elif 'result' in query or 'marks' in query:
                topic_details["subtopic"] = "results"
            elif 'admission' in query:
                topic_details["subtopic"] = "admission"
        
        # Life decisions context
        decision_words = ['kya karu', 'kya kru', 'decision', 'faisla', 'confused', 'samlajh', 'option', 'choose', 'select']
        if any(word in query for word in decision_words):
            topic_details["topic"] = "decision"
            topic_details["emotional_tone"] = "confused"
        
        # 6. Check if this continues previous topic
        if self.conversation_state["current_topic"]:
            last_topic = self.conversation_state["current_topic"]
            if topic_details["topic"] == last_topic:
                topic_details["is_new_topic"] = False
                # If we already asked questions on this topic, don't ask again
                if self.conversation_state["has_asked_questions"]:
                    topic_details["needs_clarification"] = False
        
        # 7. Check for remedy requests
        remedy_words = ['upay', 'remedy', 'solution', 'ilaj', 'totka', 'kya karu', 'kya kru', 'kaise thik', 'kaise theek']
        if any(word in query for word in remedy_words):
            return {
                "intent": "remedy_request",
                "topic_details": topic_details,
                "urgency": "medium",
                "needs_details": False,
                "language": current_language
            }
        
        # 8. Check for update/good news
        good_news_words = ['ho gaya', 'ho gayi', 'mil gaya', 'aa gaya', 'thik hai', 'accha hua', 'success', 'kamyab', 'pass', 'mila', 'mili']
        if any(phrase in query for phrase in good_news_words):
            return {
                "intent": "update",
                "topic_details": topic_details,
                "urgency": "low",
                "needs_details": False,
                "language": current_language
            }
        
        # 9. Check for simple responses
        simple_responses = ['haan', 'ha', 'yes', 'ok', 'theek', 'accha', 'hmm', 'han', 'acha', 'thik', 'no', 'nhi', 'nahi']
        if len(query.split()) <= 2 and query in simple_responses:
            return {
                "intent": "acknowledgment", 
                "urgency": "low", 
                "needs_details": False,
                "topic_details": topic_details,
                "language": current_language
            }
        
        # 10. Check for personal questions
        about_you_words = ['aap kaha', 'where are you', 'aap kaun', 'who are you', 'aap kaise', 'how are you']
        if any(phrase in query for phrase in about_you_words):
            return {
                "intent": "about_me",
                "topic_details": topic_details,
                "urgency": "low",
                "needs_details": False,
                "language": current_language
            }
        
        # Default: consultation
        return {
            "intent": "consultation",
            "topic_details": topic_details,
            "urgency": "high" if is_problem else "medium",
            "needs_details": topic_details["needs_clarification"],
            "language": current_language
        }
    

    def _get_topic_questions(self, topic, subtopic, language="hinglish"):
        """Get appropriate non-technical questions for each topic"""
        
        if language == "english":
            questions = {
                "money": {
                    "income_issue": ["How long has this been going on?", "What is your current job situation?"],
                    "default": ["How long has this financial issue been going on?", "What kind of financial help do you need?"]
                },
                "career": {
                    "job_search": ["What field do you work in?", "How long have you been looking?"],
                    "growth": ["What is your current position?", "How long have you been there?"],
                    "business": ["What type of business do you have?", "How long have you been running it?"],
                    "default": ["What field do you work in?", "What's the specific problem?"]
                },
                "legal": {
                    "legal_case": ["How long has this case been going on?", "Is it still in court?"],
                    "default": ["How long has this legal issue been going on?", "What stage is it at?"]
                },
                "love": {
                    "breakup": ["What happened?", "How long were you together?"],
                    "conflict": ["What was the fight about?", "How long has this been going on?"],
                    "marriage": ["Are you currently in a relationship?", "How long have you known each other?"],
                    "default": ["What happened?", "How long has this been going on?"]
                },
                "health": {
                    "default": ["What's the health issue?", "How long has it been going on?"]
                },
                "general": ["Tell me more about your situation.", "What exactly is concerning you?"]
            }
        elif language == "telugu":
            questions = {
                "money": {
                    "income_issue": ["Inta time nundi ee problem undi?", "Meeru ippudu em pani chestunnaru?"],
                    "default": ["Inta time nundi financial problem undi?", "Meeku ela help kavali?"]
                },
                "career": {
                    "job_search": ["Meeru e field lo pani chestaru?", "Inta time nundi try chestunnaru?"],
                    "growth": ["Ippudu meeru e position lo unnaru?", "Inta time nundi akkada unnaru?"],
                    "business": ["E type business undi?", "Inta time nundi business chestunnaru?"],
                    "default": ["Meeru e field lo pani chestaru?", "Specific ga em problem undi?"]
                },
                "legal": {
                    "legal_case": ["Inta time nundi case undi?", "Ippudu kuda court lo unda?"],
                    "default": ["Inta time nundi legal issue undi?", "Ippudu e stage lo undi?"]
                },
                "love": {
                    "breakup": ["Em jarigindi?", "Inta time kalisi unnaru?"],
                    "conflict": ["Emi vishayam meeda fight aindi?", "Inta rojulu nundi ila undi?"],
                    "marriage": ["Ippudu relationship lo unnara?", "Inta time nundi telusu?"],
                    "default": ["Em jarigindi?", "Inta time nundi ila undi?"]
                },
                "health": {
                    "default": ["Em health problem undi?", "Inta time nundi undi?"]
                },
                "general": ["Mee situation gurinchi inka cheppandi.", "Meeku em chinta undi?"]
            }
        elif language == "tamil":
            questions = {
                "money": {
                    "income_issue": ["Evvalavu naal aachu?", "Ippo enna vela seiyareengal?"],
                    "default": ["Evvalavu naal financial problem irukku?", "Enna maari help venum?"]
                },
                "career": {
                    "job_search": ["Enna field la vela seiyareengal?", "Evvalavu naal try panreengal?"],
                    "growth": ["Ippo enna position la irukkeengal?", "Evvalavu naal anga irukkeengal?"],
                    "business": ["Enna type business?", "Evvalavu naal business panreengal?"],
                    "default": ["Enna field la vela seiyareengal?", "Enna specific problem?"]
                },
                "legal": {
                    "legal_case": ["Evvalavu naal case nadakkuthu?", "Ippo court la irukka?"],
                    "default": ["Evvalavu naal legal issue irukku?", "Ippo enna stage?"]
                },
                "love": {
                    "breakup": ["Enna aachu?", "Evvalavu naal together iruntheengal?"],
                    "conflict": ["Enna vishayam fight aachu?", "Evvalavu naal ipdi irukku?"],
                    "marriage": ["Ippo relationship la irukkeengala?", "Evvalavu naal theriyum?"],
                    "default": ["Enna aachu?", "Evvalavu naal ipdi irukku?"]
                },
                "health": {
                    "default": ["Enna health problem?", "Evvalavu naal irukku?"]
                },
                "general": ["Ungal situation pathi innum sollunga.", "Ungalukku enna kavalaiya irukku?"]
            }
        else:  # hinglish (default)
            questions = {
                "money": {
                    "income_issue": ["Kitne time se yeh problem chal rahi hai?", "Aapka abhi ka job situation kya hai?"],
                    "default": ["Kitne time se financial issue hai?", "Kis tarah ki financial help chahiye?"]
                },
                "career": {
                    "job_search": ["Kis field mein kaam karte ho?", "Kitne time se try kar rahe ho?"],
                    "growth": ["Abhi kya position hai?", "Kitne time se wahan ho?"],
                    "business": ["Kis type ka business hai?", "Kitne time se chal raha hai?"],
                    "default": ["Kis field mein kaam karte ho?", "Kya specific problem hai?"]
                },
                "legal": {
                    "legal_case": ["Kitne time se case chal raha hai?", "Kya ab bhi court mein hai?"],
                    "default": ["Kitne time se legal issue hai?", "Abhi kya stage hai?"]
                },
                "love": {
                    "breakup": ["Kya hua?", "Kitne time saath the?"],
                    "conflict": ["Ladai kis baat pe hui?", "Kitne din se chal raha hai?"],
                    "marriage": ["Abhi relationship mein ho?", "Kitne time se jaante ho?"],
                    "default": ["Kya hua?", "Kitne time se chal raha hai?"]
                },
                "health": {
                    "default": ["Kya health problem hai?", "Kitne time se hai?"]
                },
                "general": ["Aur bataiye apni situation ke bare mein.", "Aapko kya chinta hai?"]
            }
        
        # Get questions for specific topic and subtopic
        if topic in questions:
            if subtopic and subtopic in questions[topic]:
                return questions[topic][subtopic]
            elif "default" in questions[topic]:
                return questions[topic]["default"]
        
        # Fallback to general questions
        return questions.get("general", ["Tell me more.", "What's on your mind?"])
    

    def _build_conversation_context(self, natal_context, transit_context, user_query, conversation_history, intent_analysis):
        """Build intelligent context based on conversation flow"""
        
        language = intent_analysis.get("language", self.conversation_state["language_preference"])
        
        context_parts = []
        
        # 1. Add natal chart summary
        if language == "english":
            context_parts.append("📜 USER'S BIRTH CHART:")
        elif language in ["telugu", "tamil", "kannada", "malayalam"]:
            context_parts.append("📜 USER KI JANMA KUNDALI:")
        else:
            context_parts.append("📜 USER KI JANMA KUNDALI:")
        
        # Extract key planetary positions
        planets_to_check = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        planet_positions = []
        
        # Find planet positions using regex
        for planet in planets_to_check:
            pattern = f"{planet}[\\s\\S]*?(?:in|is in|at)[\\s\\S]*?(\\d+[a-z]{{2}}\\s+house|[A-Z][a-z]+\\s+sign)"
            matches = re.findall(pattern, natal_context, re.IGNORECASE)
            if matches:
                planet_positions.append(f"  • {planet}: {matches[0]}")
        
        if planet_positions:
            context_parts.extend(planet_positions[:3])
        else:
            if language == "english":
                context_parts.append("  • Birth chart details available for analysis")
            else:
                context_parts.append("  • Janma kundali ke details analysis ke liye available hain")
        
        # Add ascendant if available
        asc_patterns = [r"Ascendant.*?(?:is|:)\s*([A-Z][a-z]+)", r"Lagna.*?(?:is|:)\s*([A-Z][a-z]+)"]
        for pattern in asc_patterns:
            match = re.search(pattern, natal_context, re.IGNORECASE)
            if match:
                context_parts.append(f"  • Ascendant: {match.group(1)}")
                break
        
        context_parts.append("")  # Empty line
        
        # 2. Add current transit highlights
        if language == "english":
            context_parts.append("🌌 CURRENT TRANSITS:")
        else:
            context_parts.append("🌌 CURRENT GRAH GOCHAR:")
        
        topic = intent_analysis.get("topic_details", {}).get("topic", "general")
        
        # Map topics to relevant astrological factors
        topic_mapping = {
            "money": ["Jupiter", "Venus", "2nd house", "11th house"],
            "career": ["Sun", "Saturn", "10th house"],
            "legal": ["Saturn", "Jupiter", "9th house"],
            "love": ["Venus", "Moon", "7th house"],
            "health": ["Moon", "Mars", "6th house"],
            "education": ["Mercury", "Jupiter", "5th house"],
            "decision": ["Mercury", "Moon"]
        }
        
        relevant_factors = topic_mapping.get(topic, [])
        
        # Check transit context for relevant factors
        found_factors = []
        for factor in relevant_factors:
            if factor.lower() in transit_context.lower():
                found_factors.append(factor)
        
        if found_factors:
            context_parts.append(f"  • Relevant: {', '.join(found_factors[:2])}")
        else:
            if language == "english":
                context_parts.append("  • Transit analysis available")
            else:
                context_parts.append("  • Grah gochar analysis available")
        
        context_parts.append("")  # Empty line
        
        # 3. Add conversation flow context
        if language == "english":
            context_parts.append("💭 CONVERSATION CONTEXT:")
        else:
            context_parts.append("💭 BAATCHIT KA CONTEXT:")
        
        if self.conversation_state["current_topic"]:
            context_parts.append(f"  • Current topic: {self.conversation_state['current_topic']}")
        
        # CRITICAL: Tell the AI if user has answered our questions
        if intent_analysis["intent"] == "answer_received":
            if language == "english":
                context_parts.append("  • STATUS: USER ANSWERED OUR QUESTION! GIVE INSIGHTS NOW!")
                context_parts.append("  • IMPORTANT: DO NOT ask more questions - give astrological insights!")
            else:
                context_parts.append("  • STATUS: USER NE HAMARA SAWAAL JAWAB DIYA! AB INSIGHTS DEIN!")
                context_parts.append("  • IMPORTANT: Aur sawaal mat puchen - astrological insights dein!")
        elif self.conversation_state["has_asked_questions"] and self.conversation_state["waiting_for_answer"]:
            if language == "english":
                context_parts.append("  • STATUS: Waiting for user's answer to our question")
            else:
                context_parts.append("  • STATUS: User ke jawab ka intezar hai")
        elif self.conversation_state["has_asked_questions"]:
            if language == "english":
                context_parts.append("  • STATUS: Already asked questions - ready for insights")
            else:
                context_parts.append("  • STATUS: Pahle sawaal puch chuke hain - insights ke liye taiyar")
        else:
            if language == "english":
                context_parts.append("  • STATUS: Need to ask clarifying questions first")
            else:
                context_parts.append("  • STATUS: Pehle clarifying questions puchne hain")
        
        # Add what we know about user's situation
        if self.conversation_state["user_details"]:
            if language == "english":
                context_parts.append("  • User has shared details about their situation")
            else:
                context_parts.append("  • User ne apni situation ke bare mein details batayi hain")
        
        if intent_analysis.get("topic_details", {}).get("emotional_tone"):
            context_parts.append(f"  • User's mood: {intent_analysis['topic_details']['emotional_tone']}")
        
        context_parts.append(f"  • Language: {language.upper()}")
        
        context_parts.append("")  # Empty line
        
        # 4. Add recent conversation
        if conversation_history and len(conversation_history) > 0:
            if language == "english":
                context_parts.append("🗣️ RECENT CONVERSATION:")
            else:
                context_parts.append("🗣️ PEECHLI BAATCHIT:")
            
            # Show last 4-6 messages for context
            recent = conversation_history[-6:]
            for msg in recent:
                role = "User" if msg["role"] == "user" else "You"
                content = msg["content"]
                if len(content) > 50:
                    content = content[:47] + "..."
                context_parts.append(f"  {role}: {content}")
            
            context_parts.append("")  # Empty line
        
        # 5. Add response guidance based on intent
        if language == "english":
            context_parts.append("🎯 HOW TO RESPOND:")
        else:
            context_parts.append("🎯 KAISE JAWAB DEIN:")
        
        intent = intent_analysis.get("intent", "consultation")
        topic = intent_analysis.get("topic_details", {}).get("topic", "general")
        subtopic = intent_analysis.get("topic_details", {}).get("subtopic")
        
        if intent == "answer_received":
            # USER ANSWERED OUR QUESTION - GIVE INSIGHTS!
            if language == "english":
                context_parts.append("  • USER ANSWERED OUR QUESTION! GIVE ASTROLOGICAL INSIGHTS NOW!")
                context_parts.append("  • Connect their answer to their birth chart")
                context_parts.append("  • Mention relevant planets and houses")
                context_parts.append("  • Give specific predictions and timelines")
                context_parts.append("  • DO NOT ask more questions!")
                context_parts.append("  • Example: 'Based on your chart, Venus in 2nd house...'")
            else:
                context_parts.append("  • USER NE HAMARA SAWAAL JAWAB DIYA! AB ASTROLOGICAL INSIGHTS DEIN!")
                context_parts.append("  • Unke jawab ko unki janma kundali se connect karein")
                context_parts.append("  • Relevant grah aur houses ka mention karein")
                context_parts.append("  • Specific predictions aur timelines batayein")
                context_parts.append("  • AUR SAWAAL MAT PUCHEN!")
                context_parts.append("  • Example: 'Aapki kundali ke hisaab se, 2nd house mein Shukra...'")
        
        elif intent == "greeting":
            greeting_type = intent_analysis.get("greeting_type", "first")
            if greeting_type == "first":
                if language == "english":
                    context_parts.append("  • Warm professional greeting")
                    context_parts.append("  • Introduce yourself as Astra")
                    context_parts.append("  • Ask how you can help with astrology")
                    context_parts.append("  • Example: 'Hello! I'm Astra, your astrology consultant.'")
                else:
                    context_parts.append("  • Warm professional greeting in Hinglish")
                    context_parts.append("  • Introduce as Astra, Vedic astrology consultant")
                    context_parts.append("  • Ask 'Aapko kis cheez mein help chahiye?'")
                    context_parts.append("  • Example: 'Namaste! Main Astra hoon. Aapko kya help chahiye?'")
            else:
                if language == "english":
                    context_parts.append("  • Return greeting briefly")
                    context_parts.append("  • Ask about their astrology concern")
                else:
                    context_parts.append("  • Greeting wapas dein")
                    context_parts.append("  • Puchen 'Aapko kya help chahiye?'")
        
        elif intent == "consultation":
            if intent_analysis.get("needs_details", True):
                # Get appropriate questions for this topic
                questions = self._get_topic_questions(topic, subtopic, language)
                
                if language == "english":
                    context_parts.append("  • Ask 1-2 simple, non-technical questions")
                    context_parts.append("  • Questions about their situation, NOT astrology")
                    context_parts.append(f"  • Good questions: {questions[0]}")
                    if len(questions) > 1:
                        context_parts.append(f"  • Also: {questions[1]}")
                    context_parts.append("  • Be empathetic to their emotional tone")
                    context_parts.append("  • Then WAIT for their answer")
                else:
                    context_parts.append("  • 1-2 simple, non-technical questions puchen")
                    context_parts.append("  • Astrology ke questions nahi, situation ke bare mein puchen")
                    context_parts.append(f"  • Achhe questions: {questions[0]}")
                    if len(questions) > 1:
                        context_parts.append(f"  • Aur: {questions[1]}")
                    context_parts.append("  • Unki feelings ko samjhein")
                    context_parts.append("  • Phir unke jawab ka intezar karein")
            else:
                # We have enough details - give insights
                if language == "english":
                    context_parts.append("  • Give astrological insights NOW")
                    context_parts.append("  • Connect to their birth chart")
                    context_parts.append("  • Provide specific guidance")
                    context_parts.append("  • Give timeline if possible")
                    context_parts.append("  • Use simple astrological terms")
                    context_parts.append("  • Stay on their specific topic")
                else:
                    context_parts.append("  • Ab astrological insights dein")
                    context_parts.append("  • Unki janma kundali se connect karein")
                    context_parts.append("  • Specific guidance dein")
                    context_parts.append("  • Timeline bataein if possible")
                    context_parts.append("  • Simple astrological terms use karein")
                    context_parts.append("  • Sirf unke topic pe focus karein")
        
        elif intent == "remedy_request":
            if language == "english":
                context_parts.append("  • Provide 2-3 practical remedies")
                context_parts.append("  • Be specific: what to do + when + how")
                context_parts.append("  • Example: 'Chant Shani mantra on Saturdays'")
            else:
                context_parts.append("  • 2-3 practical remedies batayein")
                context_parts.append("  • Specific batayein: kya karein + kab + kaise")
                context_parts.append("  • Example: 'Shaniwar ko Shani mantra jap karein'")
        
        elif intent == "gratitude":
            if language == "english":
                context_parts.append("  • Warm acknowledgment")
                context_parts.append("  • DO NOT give more predictions")
                context_parts.append("  • Invite for future questions")
                context_parts.append("  • Example: 'Thank you! Feel free to ask anytime, I'm here.'")
            else:
                context_parts.append("  • Warm acknowledgment")
                context_parts.append("  • Aur predictions nahi dein")
                context_parts.append("  • Future ke liye invite karein")
                context_parts.append("  • Example: 'Dhanyavaad! Kabhi bhi puch sakte hain, main yahin hoon.'")
        
        elif intent == "about_me":
            if language == "english":
                context_parts.append("  • Brief introduction about yourself")
                context_parts.append("  • Redirect to astrology consultation")
                context_parts.append("  • Example: 'I'm Astra, your astrology consultant.'")
            else:
                context_parts.append("  • Apne bare mein brief introduction")
                context_parts.append("  • Phir astrology consultation pe laein")
                context_parts.append("  • Example: 'Main Astra hoon, aapki astrology consultant.'")
        
        elif intent == "acknowledgment":
            if language == "english":
                context_parts.append("  • Acknowledge briefly")
                context_parts.append("  • Continue with appropriate response based on context")
            else:
                context_parts.append("  • Briefly acknowledge karein")
                context_parts.append("  • Context ke hisaab se appropriate response continue karein")
        
        context_parts.append("")  # Empty line
        
        # 6. Add response format instructions
        if language == "english":
            context_parts.append("📝 RESPONSE FORMAT:")
            context_parts.append("  • 1-3 short chat messages")
            context_parts.append("  • Separate with |||")
            context_parts.append("  • Sound warm and human")
            context_parts.append("  • Match user's language (English)")
            context_parts.append("  • Each message: 8-20 words maximum")
        else:
            context_parts.append("📝 JAWAB KA FORMAT:")
            context_parts.append("  • 1-3 short chat messages")
            context_parts.append("  • Separate with |||")
            context_parts.append("  • Warm aur natural sound karein")
            context_parts.append("  • User ki language match karein (Hinglish)")
            context_parts.append("  • Har message: 8-20 words maximum")
            context_parts.append("  • CORRECT HINGLISH: Use 'Aapko' not 'Aapki' for 'you'")
        
        return "\n".join(context_parts)
    

    def _update_conversation_state(self, user_query, intent_analysis, assistant_response):
        """Update conversation state based on interaction"""
        
        # Update current topic
        topic_details = intent_analysis.get("topic_details", {})
        if topic_details.get("is_new_topic", True) and topic_details.get("topic") != "general":
            self.conversation_state["current_topic"] = topic_details["topic"]
            if topic_details["topic"] not in self.conversation_state["previous_topics"]:
                self.conversation_state["previous_topics"].append(topic_details["topic"])
        
        # Store topic context
        self.conversation_state["topic_context"] = {
            "subtopic": topic_details.get("subtopic"),
            "emotional_tone": topic_details.get("emotional_tone")
        }
        
        # Update language preference
        if "language" in intent_analysis:
            self.conversation_state["language_preference"] = intent_analysis["language"]
        
        # Check if we asked questions in this response
        if '?' in assistant_response:
            self.conversation_state["has_asked_questions"] = True
            self.conversation_state["waiting_for_answer"] = True
            
            # Extract the last question from response
            questions = re.findall(r'[^|!?.]+\?', assistant_response)
            if questions:
                self.conversation_state["last_question_asked"] = questions[-1].strip()
        else:
            # If we didn't ask questions, we're not waiting for an answer
            self.conversation_state["waiting_for_answer"] = False
            self.conversation_state["last_question_asked"] = None
        
        # Check if user provided details (answered our question)
        if intent_analysis["intent"] == "answer_received":
            self.conversation_state["waiting_for_answer"] = False
            self.conversation_state["last_question_asked"] = None
            
            # Store user's answer as detail
            if self.conversation_state["current_topic"]:
                detail_key = f"{self.conversation_state['current_topic']}_answer"
                self.conversation_state["user_details"][detail_key] = user_query
        
        # Check if user provided other details
        if len(user_query.split()) > 3 and intent_analysis["intent"] not in ["greeting", "gratitude"]:
            current_topic = self.conversation_state.get("current_topic", "")
            if current_topic:
                self.conversation_state["user_details"][current_topic] = True
        
        # Reset if new topic detected
        if topic_details.get("is_new_topic", True):
            self.conversation_state["has_asked_questions"] = False
            self.conversation_state["conversation_stage"] = "initial"
            self.conversation_state["waiting_for_answer"] = False
            self.conversation_state["last_question_asked"] = None
        else:
            self.conversation_state["conversation_stage"] = "detailed"
    

    def _generate_original(self, natal_context, transit_context, user_query, conversation_history=None):
        """Main method to generate intelligent responses"""
        
        # Analyze user intent
        intent_analysis = self._analyze_query_intent(user_query, conversation_history)
        
        # Build intelligent context
        context = self._build_conversation_context(
            natal_context, 
            transit_context, 
            user_query, 
            conversation_history,
            intent_analysis
        )
        
        # Prepare the final prompt
        language = intent_analysis.get("language", self.conversation_state["language_preference"])
        
        # Language-specific instructions
        language_instructions = {
            "english": {
                "sound": "NATURAL English conversation",
                "example": "Based on your chart, Venus in 2nd house...",
                "grammar": ""
            },
            "telugu": {
                "sound": "NATURAL Telugu (romanized) conversation",
                "example": "Mee kundali prakaram, 2nd house lo Shukrudu...",
                "grammar": "Use proper Telugu: 'naaku', 'meeru', 'emi', 'ela', 'undi', 'unnadi'"
            },
            "tamil": {
                "sound": "NATURAL Tamil (romanized) conversation",
                "example": "Ungal kundali prakaram, 2nd house la Shukran...",
                "grammar": "Use proper Tamil: 'naan', 'nee', 'enna', 'eppadi', 'irukku'"
            },
            "kannada": {
                "sound": "NATURAL Kannada (romanized) conversation",
                "example": "Nimma kundali prakara, 2nd house alli Shukra...",
                "grammar": "Use proper Kannada: 'naanu', 'neevu', 'yenu', 'hege', 'ide'"
            },
            "malayalam": {
                "sound": "NATURAL Malayalam (romanized) conversation",
                "example": "Ningalude kundali prakaram, 2nd house il Shukran...",
                "grammar": "Use proper Malayalam: 'njan', 'nee', 'enthu', 'engane', 'undu'"
            },
            "hinglish": {
                "sound": "NATURAL Hinglish conversation",
                "example": "Aapki kundali ke hisaab se, 2nd house mein Shukra...",
                "grammar": "Use CORRECT HINGLISH: 'Aapko' not 'Aapki' for 'you'"
            }
        }
        
        lang_config = language_instructions.get(language, language_instructions["hinglish"])
        
        if language == "english":
            final_prompt = f"""# ASTROLOGY CONSULTATION SESSION

## CONTEXT INFORMATION:
{context}

## CURRENT USER MESSAGE:
"{user_query}"

## YOUR TASK:
Respond as Astra, the warm astrology consultant. Be natural, empathetic, and helpful.

CRITICAL INSTRUCTIONS:
• Sound like a REAL PERSON having a conversation
• Use {lang_config["sound"]}
• Be WARM and PROFESSIONAL
• Keep each message SHORT (8-20 words)
• Separate messages with |||
• Stay on astrology topic
• REMEMBER the conversation history
• If user answered your question, GIVE ASTROLOGICAL INSIGHTS immediately
• DO NOT ask the same question again
• If already asked questions and user answered, give insights now

REMEMBER: You're an astrology consultant who remembers the conversation. Be warm but professional!

Your response:"""
        else:
            # For all Indian languages (Telugu, Tamil, Hinglish, etc.)
            final_prompt = f"""# ASTROLOGY CONSULTATION SESSION

## CONTEXT INFORMATION:
{context}

## CURRENT USER MESSAGE:
"{user_query}"

## YOUR TASK:
Respond as Astra, the warm astrology consultant. Be natural, empathetic, and helpful.

CRITICAL INSTRUCTIONS:
• Sound like a REAL PERSON having a conversation
• Use {lang_config["sound"]}
• REPLY IN {language.upper()} ONLY - DO NOT MIX LANGUAGES!
• Be WARM and PROFESSIONAL
• Keep each message SHORT (8-20 words)
• Separate messages with |||
• Stay on astrology topic
• REMEMBER the conversation history
• If user answered your question, GIVE ASTROLOGICAL INSIGHTS immediately
• DO NOT ask the same question again
• If already asked questions and user answered, give insights now
• {lang_config["grammar"]}

EXAMPLE RESPONSE IN {language.upper()}:
{lang_config["example"]}

REMEMBER: You're an astrology consultant who remembers the conversation. Be warm but professional!
IMPORTANT: Reply ONLY in {language.upper()} - match the user's language exactly!

Your response:"""
        
        # Set appropriate parameters based on intent
        intent = intent_analysis.get("intent", "consultation")
        
        if intent == "gratitude":
            max_tokens = 100  # Increased for better ending
            temperature = 0.7
        elif intent == "greeting":
            max_tokens = 70
            temperature = 0.8
        elif intent == "acknowledgment":
            max_tokens = 60
            temperature = 0.75
        elif intent == "answer_received":
            max_tokens = 180  # More tokens for insights
            temperature = 0.8
        elif intent == "consultation" and intent_analysis.get("needs_details", True):
            max_tokens = 80
            temperature = 0.75
        elif intent == "about_me":
            max_tokens = 70
            temperature = 0.75
        elif intent == "remedy_request":
            max_tokens = 120
            temperature = 0.8
        else:
            max_tokens = 160  # Increased for insights
            temperature = 0.8
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.2,
                stop=None
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Clean and format response
            if response:
                # Ensure proper formatting
                response = response.replace('\n', ' ').strip()
                
                # Remove any unwanted phrases
                unwanted_phrases = ['chai peete', 'chai piye', 'coffee peete', 'coffee piye', 'tea drink']
                for phrase in unwanted_phrases:
                    response = response.replace(phrase, '')
                
                # Fix common Hinglish errors
                if language == "hinglish":
                    response = response.replace('Aapki help', 'Aapko help')
                    response = response.replace('aapki help', 'aapko help')
                    response = response.replace('Aapki chahiye', 'Aapko chahiye')
                    response = response.replace('aapki chahiye', 'aapko chahiye')
                    response = response.replace('Main pata', 'Mujhe pata')
                    response = response.replace('main pata', 'mujhe pata')
                    response = response.replace('Aapki kya', 'Aapko kya')
                    response = response.replace('aapki kya', 'aapko kya')
                
                # Ensure we have proper message separation
                if '|||' not in response and len(response.split()) > 20:
                    # Try to break into natural conversation points
                    sentences = re.split(r'[.!?]+\s*', response)
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
                    if len(sentences) > 1:
                        response = '|||'.join(sentences[:2])
                
                # Update conversation state
                self._update_conversation_state(user_query, intent_analysis, response)
                
                return response
            
            # Fallback response in appropriate language
            fallback_responses = {
                "english": [
                    "I understand. Let me check your astrological chart for insights.",
                    "Based on your situation, I can see some planetary influences at play.",
                    "Your birth chart shows some interesting patterns related to this."
                ],
                "telugu": [
                    "Artham ayindi. Ippudu mee kundali check chesta insights kosam.",
                    "Mee situation prakaram, konni grahala prabhavam kanipistundi.",
                    "Mee janma kundali lo idhi related ga konni interesting patterns unnai."
                ],
                "tamil": [
                    "Purinjuthu. Ippo ungal kundali check panren insights ku.",
                    "Ungal situation prakaram, sila grahangalin prabhavam theriyuthu.",
                    "Ungal janma kundali la idhu related ga sila interesting patterns irukku."
                ],
                "kannada": [
                    "Artha aythu. Ippo nimma kundali check madthini insights ge.",
                    "Nimma situation prakara, kelavu grahagala prabhava kanisutide.",
                    "Nimma janma kundali alli idhu related agi kelavu interesting patterns ide."
                ],
                "malayalam": [
                    "Manasilayi. Ippo ningalude kundali check cheyyam insights nu.",
                    "Ningalude situation prakaram, chila grahangalude prabhavam kaanunnu.",
                    "Ningalude janma kundali il ithu related aayi chila interesting patterns undu."
                ],
                "hinglish": [
                    "Samajh gaya. Ab main aapki kundali check karta hoon insights ke liye.",
                    "Aapki situation ke hisaab se, kuch grahon ke prabhav dikh rahe hain.",
                    "Aapki janma kundali mein isse related kuch interesting patterns hain."
                ]
            }
            
            import random
            fallbacks = fallback_responses.get(language, fallback_responses["hinglish"])
            fallback_response = random.choice(fallbacks)
            
            # Update state with fallback
            self._update_conversation_state(user_query, intent_analysis, fallback_response)
            
            return fallback_response
            
        except Exception as e:
            logger.info("Error in LLM call: {str(e)}")
            error_messages = {
                "english": "There seems to be a connection issue. Please try again in a moment.",
                "telugu": "Connection lo konchem problem undi. Konchem sepu taruvata try cheyandi.",
                "tamil": "Connection la konjam problem irukku. Konjam neram kalichi try pannunga.",
                "kannada": "Connection alli swalpa problem ide. Swalpa samaya kaleyalli try madi.",
                "malayalam": "Connection il kochu problem undu. Kochu samayam kazhinje try cheyyuka.",
                "hinglish": "Connection mein thodi problem hai. Thodi der baad phir try karein."
            }
            return error_messages.get(language, error_messages["hinglish"])


    def reset_conversation(self):
        """Reset conversation state"""
        self.conversation_state = {
            "current_topic": None,
            "has_asked_questions": False,
            "user_details": {},
            "conversation_stage": "initial",
            "previous_topics": [],
            "language_preference": "hinglish",
            "last_question_asked": None,
            "waiting_for_answer": False,
            "topic_context": {}
        }


# Backward compatibility alias
EnhancedLLMBridge = LLMBridge
