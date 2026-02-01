"""
Render Deployment Entry Point
Isolated from main system - imports from main codebase
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import from main codebase
from src.core.astro_engine import AstroEngine
from src.core.llm_bridge import LLMBridge
from src.utils.characters import get_all_characters, build_character_prompt, HARDCODED_CHARACTERS
from src.utils.remedies import get_planet_remedy, get_all_planet_remedies
from src.utils.logger import setup_logger

# Import local database
from database import SimpleDatabase

logger = setup_logger(__name__)

# ==================== PROMPT VERSIONS FOR TESTING ====================
PROMPT_VERSIONS = {
    "v1": {
        "name": "v1 - Language Adaptation",
        "description": "Focus on language matching + question guidelines",
        "prompt": """You are Astra — a warm, empathetic Vedic astrology consultant. You adapt your language to match the user's language EXACTLY.

LANGUAGE ADAPTATION:
- ALWAYS reply in the SAME language the user is using
- If user speaks in Telugu, reply ONLY in Telugu (romanized)
- If user speaks in Tamil, reply ONLY in Tamil (romanized)
- If user speaks in Hindi/Hinglish, reply in Hinglish
- If user speaks in English, reply in English
- DO NOT mix languages!

CORRECT USAGE:
- Hinglish: Use "Aapko" not "Aapki", "Mujhe" not "Main"
- Telugu: naaku, meeru, emi, ela
- Tamil: naan, nee, enna, eppadi

QUESTION GUIDELINES:
- Ask ONLY practical, non-technical questions
- NO astrological jargon in questions
- Ask 1-2 questions MAX, then wait for answer

EXAMPLES:
User: "Meri job ki problem hai"
You: "Kis field mein kaam karte ho?|||Kitne time se problem hai?"

User (Telugu): "Naaku naa udyogam gurinchi matladali"
You: "Meeru e field lo pani chestunnaru?|||Inta time nundi problem undi?"

FORMAT: 1-3 short messages with "|||", 8-20 words each
"""
    },
    "v2": {
        "name": "v2 - Identity Protection",
        "description": "Strong identity guard + language rules",
        "prompt": """You are Astra — a warm, empathetic Vedic astrology consultant.

IDENTITY (CRITICAL):
- YOU ARE ASTRA - A VEDIC ASTROLOGY CONSULTANT. THIS IS YOUR ONLY IDENTITY.
- NEVER mention being AI, chatbot, LLM, GPT, or any AI system
- IF ASKED "are you AI?": Reply "Main Astra hoon, aapka Vedic jyotish guide"
- REDIRECT to astrology: "Aapke jeevan ke baare mein baat karte hain"
- Your knowledge comes from "Vedic astrology wisdom and cosmic observations"

LANGUAGE:
- Reply in user's language ONLY
- Hinglish: "Aapko" not "Aapki", "Mujhe" not "Main"
- Telugu/Tamil: Use proper romanization

CONTEXT:
- REMEMBER previous messages
- If user answers your question, GIVE INSIGHTS immediately
- Don't repeat questions

QUESTIONS:
- Ask practical questions about their situation
- NO astrological jargon
- 1-2 questions MAX

FORMAT: 1-3 short messages with "|||", 8-20 words each
"""
    },
    "v3": {
        "name": "v3 - Emotional Support",
        "description": "Soft language, phase-based guidance, emotional clarity",
        "prompt": """You are Astra, a warm and empathetic Vedic astrology consultant.

Speak in the user's dominant language and tone naturally.
Allow mixed language if the user mixes languages.

YOUR ROLE:
- Offer emotional support
- Ask practical, real-life questions when clarity is needed
- Give gentle, phase-based astrological guidance (not predictions)

CONVERSATION FLOW:
- Ask at most 1–2 questions only if needed
- After the user responds, shift to guidance
- Do not keep asking questions repeatedly

ASTROLOGY STYLE:
- Use soft, non-technical language like:
  "iss phase mein", "iss waqt", "aane wale time mein"
- Avoid planet names or astrological jargon unless asked
- Frame astrology as guidance, not certainty

LANGUAGE STYLE:
- Keep Hinglish natural and conversational
- Do not force grammar rules unnaturally
- Match the user's comfort level

SAFETY:
- Avoid absolute claims or life-altering instructions
- Encourage reflection, not dependency

FORMAT: 1-3 short messages with "|||", 8-20 words each
Stay consistent, calm, and human.
"""
    },
    "v4": {
        "name": "v4 - Human First + Astrology Translation",
        "description": "React like human first, translate astrology to phases",
        "prompt": """You are Astra, a warm Vedic astrology consultant.

RULE 1: REACT LIKE A HUMAN FIRST
Before ANY advice, react like a real person would:
- "Hmm, samajh sakta hoon yeh mushkil hai"
- "Achha, toh career ke baare mein baat karni hai"
Advice is OPTIONAL. Presence is MANDATORY.

RULE 2: TRANSLATE ASTROLOGY TO PHASES
NEVER say raw astrology. ALWAYS translate to timing/phases.
BAD: "Saturn 10th house mein hai"
GOOD: "Iss phase mein career thoda slow hai"

RULE 3: MIRROR THEIR ENERGY
- If casual: "Haan yaar, dekh..."
- If formal: "Ji, aapki kundali mein..."
- If anxious: Slow down, reassure first

FORMAT: 1-3 short messages with "|||", 8-20 words each
LANGUAGE: User's language ONLY
"""
    },
    "v5": {
        "name": "v5 - Question First + Multi-Language",
        "description": "Ask 1-2 questions before readings, adapts to all languages",
        "prompt": """You are Astra, a warm Vedic astrology consultant.

═══════════════════════════════════════════════════════════
LANGUAGE RULE (CRITICAL):
═══════════════════════════════════════════════════════════
Reply in the SAME language the user is using. DO NOT mix languages!
- Telugu user → Reply ONLY in Telugu (romanized)
- Tamil user → Reply ONLY in Tamil (romanized)
- Kannada user → Reply ONLY in Kannada (romanized)
- Hindi/Hinglish user → Reply in Hinglish
- English user → Reply in English

CORRECT GRAMMAR:
- Hinglish: "Aapko" not "Aapki", "Mujhe" not "Main"
- Telugu: naaku, meeru, emi, ela, cheppandi
- Tamil: naan, nee, enna, eppadi, sollunga
- Kannada: naanu, neevu, enu, hege, heli

═══════════════════════════════════════════════════════════
CORE RULE: ASK BEFORE YOU ADVISE
═══════════════════════════════════════════════════════════
Before giving any reading:
1. Acknowledge what they said
2. Ask 1-2 practical questions about their situation
3. WAIT for their answer
4. THEN give astrological insights

BAD: User asks something → You immediately give planet/house predictions
GOOD: User asks something → You first ask about their situation

═══════════════════════════════════════════════════════════
QUESTION EXAMPLES BY LANGUAGE:
═══════════════════════════════════════════════════════════
HINGLISH:
Career: "Kis field mein kaam karte ho?|||Kitne time se problem hai?"
Love: "Relationship mein ho ya koi specific person hai?"
Money: "Kya specific tension hai - income ya savings?"

TELUGU:
Career: "Meeru e field lo pani chestunnaru?|||Inta time nundi problem undi?"
Love: "Relationship lo unnara leda koi specific person aa?"
Money: "Specific ga emi tension - income aa savings aa?"

TAMIL:
Career: "Neenga enna field la vela seiyareengal?|||Evvalavu naal problem irukku?"
Love: "Relationship la irukkingala illa yaaraavathu special person aa?"
Money: "Enna specific tension - income aa savings aa?"

KANNADA:
Career: "Neevu yava field alli kelsa madthira?|||Estu samaya indha problem ide?"
Love: "Relationship alli iddira illa yaraadru special person aa?"
Money: "Enu specific tension - income aa savings aa?"

═══════════════════════════════════════════════════════════
AFTER THEY ANSWER - GIVE INSIGHTS:
═══════════════════════════════════════════════════════════
Use phase-based language, not raw astrology:
- "Iss phase mein..." / "Ee phase lo..." / "Indha phase la..."
- "Aane wale time mein..." / "Vastunna time lo..."
- Translate planets to meanings, not jargon

FORMAT: 1-3 short messages with "|||", 8-20 words each
"""
    },
    "v6": {
        "name": "v6 - Empathy & Grounding",
        "description": "Presence before prediction, ground anxious users",
        "prompt": """You are Astra, a warm Vedic astrology consultant.

CORE RULE: PRESENCE BEFORE PREDICTION
When someone comes to you, they need to feel HEARD first.

STEP 1 - ACKNOWLEDGE: "Hmm, samajh sakta hoon", "Yeh tension hona normal hai"
STEP 2 - ASK (if needed): "Kya specifically pareshan kar raha hai?"
STEP 3 - GROUND (if anxious): "Dekho, itna bura nahi hai jitna lag raha"
STEP 4 - GUIDE: Give phase-based insight

EXAMPLES:
User ANXIOUS: "Mujhe bahut tension ho rahi hai career ki"
You: "Sun, tension mat le|||Tera chart dekha - koi major block nahi hai|||Bas yeh phase thoda slow hai"

User SAD: "Breakup ho gaya"
You: "Yaar, breakup hurt karta hai|||Tumhari Venus challenging phase mein hai|||But yeh closure bhi ho sakta hai - better ke liye"

WHAT NOT TO DO:
❌ Jump straight to predictions when upset
❌ Use scary terms: "Shani ki sade-sati"
❌ Ignore their emotions

FORMAT: 1-3 short messages with "|||", 8-20 words each
LANGUAGE: User's language ONLY
"""
    },
    "v7": {
        "name": "v7 - Personalized + Actionable",
        "description": "Use their words, end with action they can take",
        "prompt": """You are Astra, a warm Vedic astrology consultant.

CORE RULE: MAKE IT PERSONAL + ACTIONABLE
Generic astrology = Useless. Personal + Actionable = Real guidance.

1. Reference THEIR situation (use their words back)
2. End with something they can DO

BAD: "Career accha rahega, mehnat karo"
GOOD: User said "IT job mein 3 saal stuck" → You: "IT mein 3 saal frustrating hota hai|||Saturn slow growth deta hai|||Switch karna hai toh iss year sahi hai"

ACTIONABLE ENDINGS:
Career: "Iss week LinkedIn update kar", "Boss se directly baat kar"
Love: "Ek date plan karo", "Pehle khud clear ho kya chahiye"
Money: "Emergency fund start kar", "Iss month spending rok"
Health: "30 min walk add kar", "Doctor se checkup karwa"

RESPONSE STRUCTURE:
Message 1: Acknowledge/Connect to their situation
Message 2: Astrological insight (phase-based)
Message 3: Actionable suggestion

FORMAT: 1-3 short messages with "|||", 8-20 words each
LANGUAGE: User's language ONLY
"""
    },
    "current": {
        "name": "Current (Production)",
        "description": "Current prompt in llm_bridge.py",
        "prompt": None  # Will use default from llm_bridge
    }
}

# Get the directory where this file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=os.path.join(current_dir, 'static'))
CORS(app)

# Initialize components
astro = AstroEngine()
llm = LLMBridge()
db = SimpleDatabase()  # Initialize database

logger.info("Database initialized. Stats: " + str(db.get_stats()))

# API Key (optional - set in Render environment)
API_KEY = os.environ.get('ASTRA_API_KEY', None)


def require_api_key(f):
    """Optional API key authentication"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not API_KEY:
            return f(*args, **kwargs)

        key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if key != API_KEY:
            return jsonify({"success": False, "error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def home():
    """Serve the frontend HTML"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)


@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        "service": "ASTRA Vedic Astrology API",
        "version": "2.0.0-test",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "characters": "GET /api/v1/characters",
            "chat": "POST /api/v1/chat",
            "remedies": "GET /api/v1/remedies/<planet>"
        },
        "docs": "See /api/v1/chat for request format"
    })


@app.route('/health')
def health():
    """Health check with database stats"""
    db_stats = db.get_stats()
    return jsonify({
        "success": True,
        "status": "healthy",
        "services": {
            "llm": "available" if llm and llm.client else "unavailable",
            "astro_engine": "ready" if astro else "unavailable",
            "database": "connected"
        },
        "database": db_stats
    })


@app.route('/api/v1/prompts', methods=['GET'])
@require_api_key
def get_prompts():
    """Get available prompt versions for testing"""
    try:
        prompts_list = []
        for prompt_id, info in PROMPT_VERSIONS.items():
            prompts_list.append({
                "id": prompt_id,
                "name": info["name"],
                "description": info["description"]
            })
        return jsonify({"success": True, "prompts": prompts_list, "count": len(prompts_list)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/characters', methods=['GET'])
@require_api_key
def get_characters():
    """Get available characters"""
    try:
        characters = get_all_characters()
        chars_list = []
        for char_id, info in characters.items():
            chars_list.append({
                "id": char_id,
                "name": info.get("name"),
                "specialty": info.get("description"),
                "emoji": info.get("emoji", "")
            })
        return jsonify({"success": True, "characters": chars_list, "count": len(chars_list)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/remedies/<planet>', methods=['GET'])
@require_api_key
def get_remedies(planet):
    """Get remedies for a planet"""
    try:
        remedy = get_planet_remedy(planet)
        if remedy:
            return jsonify({"success": True, "planet": planet, "remedies": remedy})
        return jsonify({"success": False, "error": f"Planet '{planet}' not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/remedies', methods=['GET'])
@require_api_key
def get_all_remedies():
    """Get all planet remedies"""
    try:
        remedies = get_all_planet_remedies()
        return jsonify({"success": True, "remedies": remedies})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/chat', methods=['POST'])
@require_api_key
def chat():
    """
    AstroVoice Integration Endpoint (EXACT MATCH)

    Receives birth data AND character data directly from AstroVoice.

    Request:
    {
        "user_id": 1,
        "query": "When will I get married?",
        "session_id": "session_123",

        // Character Data (Required) - provided by AstroVoice
        "character": {
            "id": "marriage",
            "name": "Pandit Ravi Sharma",
            "age": 52,
            "experience": 25,
            "specialty": "Marriage & Relationships",
            "language_style": "traditional",
            "about": "An experienced traditional astrologer specializing in marriage"
        },

        // Birth Data (Required)
        "name": "Rahul",
        "birth_date": "15/08/1990",
        "birth_time": "14:30",
        "birth_location": "Mumbai, India",
        "latitude": 19.076,
        "longitude": 72.877,
        "timezone": "Asia/Kolkata",

        // Optional - Conversation History
        "conversation_history": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Namaste! How can I help?"}
        ]
    }

    Response:
    {
        "success": true,
        "response": "Achha Rahul, looking at your chart...",
        "character": {
            "id": "marriage",
            "name": "Pandit Ravi Sharma"
        },
        "session_id": "session_123"
    }
    """
    try:
        data = request.json

        # Validate REQUIRED fields (exact match with AstroVoice spec)
        required_fields = [
            'user_id', 'query', 'session_id', 'character',
            'name', 'birth_date', 'birth_time', 'birth_location',
            'latitude', 'longitude', 'timezone'
        ]

        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Extract data
        user_id = data['user_id']
        query = data['query']
        session_id = data['session_id']

        # Character data from AstroVoice (REQUIRED)
        character_data = data['character']
        if not isinstance(character_data, dict):
            return jsonify({
                "success": False,
                "error": "character must be an object with id, name, age, experience, specialty, etc."
            }), 400

        # Validate character has required fields
        character_required = ['id', 'name']
        missing_char_fields = [f for f in character_required if f not in character_data]
        if missing_char_fields:
            return jsonify({
                "success": False,
                "error": f"character missing required fields: {', '.join(missing_char_fields)}"
            }), 400

        character_id = character_data['id']
        character_name = character_data['name']

        # Optional: Conversation history for context
        conversation_history = data.get('conversation_history', [])

        # Birth data
        name = data['name']
        birth_date = data['birth_date']
        birth_time = data['birth_time']
        birth_location = data['birth_location']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        timezone = data['timezone']

        # Parse birth date (DD/MM/YYYY)
        day, month, year = map(int, birth_date.split('/'))

        # Parse birth time (HH:MM)
        hour, minute = map(int, birth_time.split(':'))

        # Create natal chart from provided data
        natal_chart = astro.create_natal_chart(
            name, year, month, day, hour, minute,
            birth_location, latitude, longitude, timezone
        )

        # Get astrological context
        natal_context = astro.build_natal_context(natal_chart)
        transit_chart = astro.get_transit_chart(
            birth_location, latitude, longitude, timezone
        )
        transit_context = astro.build_transit_context(transit_chart, natal_chart)

        # Generate response with character data and conversation history
        result = llm.generate_response(
            user_id=user_id,
            user_query=query,
            natal_context=natal_context,
            transit_context=transit_context,
            session_id=session_id,
            character_id=character_id,
            conversation_history=conversation_history,
            character_data=character_data  # Pass full character data
        )

        response = result['response']

        # Response format (exact match with AstroVoice spec)
        return jsonify({
            "success": True,
            "response": response,
            "character": {
                "id": character_id,
                "name": character_name
            },
            "session_id": session_id
        })

    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400

    except Exception as e:
        logger.error(f"AstroVoice chat endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/chat/simple', methods=['POST'])
@require_api_key
def chat_simple():
    """
    Simplified Chat Endpoint for Frontend Testing
    
    Request:
    {
        "message": "When will I get married?",
        "birth_data": {
            "name": "Rahul",
            "birth_date": "1990-08-15",
            "birth_time": "14:30",
            "birth_location": "Mumbai, India"
        },
        "character_data": {
            "character_name": "marriage",
            "preferred_language": "Hinglish"
        },
        "conversation_history": []
    }
    """
    try:
        from geopy.geocoders import Nominatim
        from timezonefinder import TimezoneFinder
        from datetime import datetime
        
        data = request.json
        
        # Extract data
        message = data.get('message', '').strip()
        birth_data = data.get('birth_data', {})
        character_data = data.get('character_data', {})
        session_id = data.get('session_id', None)  # Optional session ID from frontend
        
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        if not birth_data:
            return jsonify({"success": False, "error": "Birth data is required"}), 400
        
        # Extract birth data
        name = birth_data.get('name', 'User')
        birth_date = birth_data.get('birth_date')
        birth_time = birth_data.get('birth_time')
        birth_location = birth_data.get('birth_location')
        
        if not all([birth_date, birth_time, birth_location]):
            return jsonify({
                "success": False, 
                "error": "Birth date, time, and location are required"
            }), 400
        
        # Geocode location with increased timeout
        try:
            geolocator = Nominatim(user_agent="astra-astrology", timeout=10)
            location = geolocator.geocode(birth_location)
            
            if not location:
                return jsonify({
                    "success": False,
                    "error": f"Could not find location: {birth_location}"
                }), 400
            
            latitude = location.latitude
            longitude = location.longitude
        except Exception as geo_error:
            logger.error(f"Geocoding error for {birth_location}: {str(geo_error)}")
            return jsonify({
                "success": False,
                "error": f"Location service temporarily unavailable. Please try again."
            }), 503
        
        # Get timezone
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=latitude, lng=longitude)
        
        if not timezone:
            timezone = "UTC"
        
        # Find or create user in database
        user_id = db.find_or_create_user(
            name=name,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_location=birth_location,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )
        
        # Generate session ID if not provided
        if not session_id:
            import hashlib
            session_id = hashlib.md5(f"{user_id}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # Character handling
        character_name = character_data.get('character_name', 'general')
        preferred_language = character_data.get('preferred_language', 'Hinglish')

        # Prompt version handling (for A/B testing)
        prompt_version = data.get('prompt_version', 'current')
        selected_prompt = None
        if prompt_version in PROMPT_VERSIONS and PROMPT_VERSIONS[prompt_version]['prompt']:
            selected_prompt = PROMPT_VERSIONS[prompt_version]['prompt']
            logger.info(f"Using prompt version: {prompt_version}")

        # Create or update session
        db.create_or_update_session(session_id, user_id, character_name, preferred_language)
        
        # Get conversation history from database for this session
        conversation_history = db.get_session_history(session_id, limit=20)
        
        # Parse birth date (YYYY-MM-DD)
        year, month, day = map(int, birth_date.split('-'))
        
        # Parse birth time (HH:MM)
        hour, minute = map(int, birth_time.split(':'))
        
        logger.info(f"User {user_id} | Session {session_id} | Message: {message[:50]}...")
        
        # Create natal chart
        natal_chart = astro.create_natal_chart(
            name, year, month, day, hour, minute,
            birth_location, latitude, longitude, timezone
        )
        
        # Get astrological context
        natal_context = astro.build_natal_context(natal_chart)
        transit_chart = astro.get_transit_chart(
            birth_location, latitude, longitude, timezone
        )
        transit_context = astro.build_transit_context(transit_chart, natal_chart)
        
        # Build character data for LLM
        full_character_data = {
            'id': character_name,
            'name': character_name,
            'preferred_language': preferred_language
        }

        # Override system prompt if testing a specific version
        original_prompt = llm.system_prompt
        if selected_prompt:
            llm.system_prompt = selected_prompt

        # Generate response with database-retrieved history
        result = llm.generate_response(
            user_id=user_id,
            user_query=message,
            natal_context=natal_context,
            transit_context=transit_context,
            session_id=session_id,
            character_id=character_name,
            conversation_history=conversation_history,
            character_data=full_character_data
        )

        # Restore original prompt
        if selected_prompt:
            llm.system_prompt = original_prompt

        response = result['response']
        
        # Save conversation to database
        db.add_conversation(
            user_id=user_id,
            session_id=session_id,
            query=message,
            response=response,
            character_id=character_name,
            language=preferred_language
        )
        
        logger.info(f"Saved conversation to DB. User: {user_id}, Session: {session_id}")
        
        return jsonify({
            "success": True,
            "response": response,
            "session_id": session_id,
            "user_id": user_id,
            "prompt_version": prompt_version
        })
        
    except Exception as e:
        logger.error(f"Simple chat endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    logger.info(f"Starting ASTRA API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
