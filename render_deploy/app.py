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
    Main chat endpoint - AstroVoice compatible

    Request body:
    {
        "user_id": 1,
        "query": "When will I get married?",
        "session_id": "session_123",

        // Character (required)
        "character": {
            "id": "marriage",
            "name": "Pandit Ravi Sharma",
            "age": 52,
            "experience": 25,
            "specialty": "Marriage",
            "language_style": "traditional",
            "about": "Marriage specialist"
        },

        // OR use character_id for hardcoded characters
        "character_id": "marriage",

        // Birth data (required)
        "name": "Rahul",
        "birth_date": "15/08/1990",
        "birth_time": "14:30",
        "birth_location": "Mumbai, India",
        "latitude": 19.076,
        "longitude": 72.877,
        "timezone": "Asia/Kolkata",

        // Optional
        "conversation_history": []
    }
    """
    try:
        data = request.json

        # Required fields
        required = ['user_id', 'query', 'session_id', 'name', 'birth_date', 'birth_time',
                   'birth_location', 'latitude', 'longitude', 'timezone']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            return jsonify({"success": False, "error": f"Missing: {', '.join(missing)}"}), 400

        # Extract data
        user_id = data['user_id']
        query = data['query']
        session_id = data['session_id']

        # Character - either full object or ID
        character_data = data.get('character')
        character_id = data.get('character_id', 'general')

        if not character_data and character_id:
            # Use hardcoded character
            if character_id in HARDCODED_CHARACTERS:
                character_data = HARDCODED_CHARACTERS[character_id]

        # Birth data
        name = data['name']
        birth_date = data['birth_date']
        birth_time = data['birth_time']
        location = data['birth_location']
        lat = float(data['latitude'])
        lon = float(data['longitude'])
        tz = data['timezone']

        # Parse date/time
        day, month, year = map(int, birth_date.split('/'))
        hour, minute = map(int, birth_time.split(':'))

        # Conversation history
        history = data.get('conversation_history', [])

        # Create chart
        natal_chart = astro.create_natal_chart(name, year, month, day, hour, minute, location, lat, lon, tz)
        natal_context = astro.build_natal_context(natal_chart)

        # Get transits
        transit_chart = astro.get_transit_chart(location, lat, lon, tz)
        transit_context = astro.build_transit_context(transit_chart, natal_chart)

        # Generate response
        result = llm.generate_response(
            user_id=user_id,
            user_query=query,
            natal_context=natal_context,
            transit_context=transit_context,
            session_id=session_id,
            character_id=character_id,
            conversation_history=history,
            character_data=character_data
        )

        response = result.get('response', '')
        cache_stats = result.get('cache_stats', {})

        return jsonify({
            "success": True,
            "response": response,
            "character": {
                "id": character_data.get('id', character_id) if character_data else character_id,
                "name": character_data.get('name', 'Astra') if character_data else 'Astra'
            },
            "session_id": session_id,
            "cache": {
                "hit_rate": cache_stats.get('cache_hit_rate', 0),
                "cached_tokens": cache_stats.get('cached_tokens', 0),
                "total_tokens": cache_stats.get('total_input_tokens', 0)
            }
        })

    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid format: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    logger.info(f"Starting ASTRA API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
