"""
Render Deployment Entry Point
Isolated from main system - imports from main codebase
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import from main codebase
from src.core.astro_engine import AstroEngine
from src.core.llm_bridge import LLMBridge
from src.utils.characters import get_all_characters, build_character_prompt, HARDCODED_CHARACTERS
from src.utils.remedies import get_planet_remedy, get_all_planet_remedies
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components
astro = AstroEngine()
llm = LLMBridge()

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
    """Home page with API info"""
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
    """Health check"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "services": {
            "llm": "available" if llm and llm.client else "unavailable",
            "astro_engine": "ready" if astro else "unavailable"
        }
    })


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    logger.info(f"Starting ASTRA API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
