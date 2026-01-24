from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from src.core.astro_engine import AstroEngine
from src.core.llm_bridge import EnhancedLLMBridge  # With caching!
from src.utils import config
import os

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

"""
NOTE: Database removed - all user/birth data provided by AstroVoice integration.
Main endpoint: /api/v1/chat (receives birth data in request)
"""

app = Flask(__name__)
CORS(app)

# Initialize components (no database)
astro = AstroEngine()
llm = EnhancedLLMBridge()  # Enhanced with caching, no DB

# Interactive frontend HTML template
HOME_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ASTRA - AI Vedic Astrology</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 3em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            flex: 1;
            padding: 15px;
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s;
        }
        .tab:hover { background: rgba(255,255,255,0.3); }
        .tab.active { background: white; color: #764ba2; font-weight: bold; }
        
        .panel {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .panel.active { display: block; }
        
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .users-list {
            display: grid;
            gap: 15px;
            margin-bottom: 20px;
        }
        .user-card {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            cursor: pointer;
            transition: all 0.3s;
        }
        .user-card:hover { background: #e9ecef; transform: translateX(5px); }
        .user-card.selected { background: #667eea; color: white; }
        
        .chat-container {
            height: 500px;
            display: flex;
            flex-direction: column;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
        }
        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
        }
        .message.assistant {
            background: white;
            color: #333;
            border: 1px solid #ddd;
        }
        .chat-input-group {
            display: flex;
            gap: 10px;
        }
        .chat-input-group input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            font-weight: 500;
        }
        .alert.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ASTRA</h1>
            <p>Your AI-Powered Vedic Astrology Companion</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('create')">Create Birth Chart</button>
            <button class="tab" onclick="showTab('users')">My Charts</button>
            <button class="tab" onclick="showTab('chat')">Chat with Astra</button>
        </div>
        
        <!-- Create User Panel -->
        <div id="create-panel" class="panel active">
            <h2 style="margin-bottom: 20px; color: #764ba2;">Create New Birth Chart</h2>
            <div id="create-alert"></div>
            <form id="create-form">
                <div class="form-group">
                    <label>Your Name</label>
                    <input type="text" id="name" placeholder="Enter your name" required>
                </div>
                <div class="form-group">
                    <label>Birth Date (DD/MM/YYYY)</label>
                    <input type="text" id="birth_date" placeholder="15/08/1990" required>
                </div>
                <div class="form-group">
                    <label>Birth Time (HH:MM in 24-hour format)</label>
                    <input type="text" id="birth_time" placeholder="14:30" required>
                </div>
                <div class="form-group">
                    <label>Birth Location</label>
                    <input type="text" id="location" placeholder="Mumbai, India" required>
                </div>
                <button type="submit" class="btn" id="create-btn">Generate Birth Chart</button>
            </form>
        </div>
        
        <!-- Users List Panel -->
        <div id="users-panel" class="panel">
            <h2 style="margin-bottom: 20px; color: #764ba2;">Your Birth Charts</h2>
            <div id="users-alert"></div>
            <div id="users-list" class="users-list"></div>
        </div>
        
        <!-- Chat Panel -->
        <div id="chat-panel" class="panel">
            <h2 style="margin-bottom: 20px; color: #764ba2;">Chat with Astra</h2>
            <div id="chat-alert"></div>

            <!-- Character Selector -->
            <div style="margin-bottom: 15px;">
                <label style="font-weight: 500; margin-bottom: 8px; display: block; color: #555;">Choose Your Guide:</label>
                <div id="character-selector" style="display: flex; gap: 10px; flex-wrap: wrap;"></div>
            </div>

            <div class="chat-container">
                <div class="chat-messages" id="chat-messages">
                    <div class="alert info">Select a birth chart from "My Charts" to start chatting!</div>
                </div>
                <div class="chat-input-group">
                    <input type="text" id="chat-input" placeholder="Ask Astra anything..." disabled>
                    <button class="btn" id="chat-btn" onclick="sendMessage()" disabled>Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedUserId = null;
        let currentSessionId = null;  // NEW: Track current chat session
        let selectedCharacter = 'general';  // NEW: Track selected character (default: general)
        let availableCharacters = {};  // NEW: Store available characters

        // Generate unique session ID
        function generateSessionId() {
            return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }

        // Load available characters
        async function loadCharacters() {
            try {
                console.log('Loading characters...');
                const response = await fetch('/api/characters');
                const result = await response.json();
                console.log('Characters API response:', result);

                if (result.success) {
                    availableCharacters = result.characters;
                    console.log('Available characters:', Object.keys(availableCharacters));
                    renderCharacterSelector();
                } else {
                    console.error('Characters API failed:', result.error);
                    document.getElementById('character-selector').innerHTML = '<span style="color: red;">Failed to load characters</span>';
                }
            } catch (error) {
                console.error('Failed to load characters:', error);
                document.getElementById('character-selector').innerHTML = '<span style="color: red;">Error loading characters: ' + error.message + '</span>';
            }
        }

        // Render character selector buttons
        function renderCharacterSelector() {
            const selector = document.getElementById('character-selector');
            selector.innerHTML = '';

            Object.keys(availableCharacters).forEach(charId => {
                const char = availableCharacters[charId];
                const btn = document.createElement('button');
                btn.className = 'btn' + (charId === selectedCharacter ? ' active' : '');
                btn.innerHTML = char.description;
                btn.title = char.name;
                btn.style.cssText = 'padding: 8px 16px; font-size: 14px; flex: 0 1 auto;' +
                                    (charId === selectedCharacter ? ' background: #667eea; color: white;' : ' background: white; color: #667eea; border: 2px solid #667eea;');
                btn.onclick = () => selectCharacter(charId);
                selector.appendChild(btn);
            });
        }

        // Select character
        function selectCharacter(charId) {
            selectedCharacter = charId;
            renderCharacterSelector();

            // Generate new session ID for fresh conversation with new character
            currentSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

            // Clear chat and show character change notification
            const char = availableCharacters[charId];
            const messages = document.getElementById('chat-messages');
            if (selectedUserId) {
                // Clear previous conversation and start fresh with new character
                messages.innerHTML = '<div class="alert info" style="font-size: 13px;">Now talking to: <strong>'+char.name+'</strong> ('+char.description+' specialist)<br><small>Conversation reset - start fresh!</small></div>';
                messages.scrollTop = messages.scrollHeight;
            }
        }

        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tab + '-panel').classList.add('active');
            
            if (tab === 'users') loadUsers();
        }
        
        // Create User Form
        document.getElementById('create-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('create-btn');
            const alert = document.getElementById('create-alert');
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loading"></span> Creating...';
            alert.innerHTML = '';
            
            const data = {
                name: document.getElementById('name').value,
                birth_date: document.getElementById('birth_date').value,
                birth_time: document.getElementById('birth_time').value,
                location: document.getElementById('location').value
            };
            
            try {
                const response = await fetch('/api/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert.innerHTML = '<div class="alert success">✓ Birth chart created successfully! User ID: ' + result.user_id + '</div>';
                    document.getElementById('create-form').reset();
                } else {
                    alert.innerHTML = '<div class="alert error">✗ Error: ' + result.error + '</div>';
                }
            } catch (error) {
                alert.innerHTML = '<div class="alert error">✗ Failed to create birth chart. Please try again.</div>';
            }
            
            btn.disabled = false;
            btn.textContent = 'Generate Birth Chart';
        });
        
        // Load Users
        async function loadUsers() {
            const list = document.getElementById('users-list');
            const alert = document.getElementById('users-alert');
            
            list.innerHTML = '<p>Loading...</p>';
            alert.innerHTML = '';
            
            try {
                const response = await fetch('/api/users');
                const result = await response.json();
                
                if (result.success && result.users.length > 0) {
                    list.innerHTML = result.users.map(user => `
                        <div class="user-card ${selectedUserId === user.user_id ? 'selected' : ''}" onclick="selectUser(${user.user_id})">
                            <strong>${user.name}</strong><br>
                            <small>Born: ${user.birth_date} | ID: ${user.user_id}</small>
                        </div>
                    `).join('');
                } else {
                    list.innerHTML = '<div class="alert info">No birth charts yet. Create one first!</div>';
                }
            } catch (error) {
                alert.innerHTML = '<div class="alert error">Failed to load users</div>';
            }
        }
        
        // Select User
        function selectUser(userId) {
            selectedUserId = userId;
            currentSessionId = generateSessionId();  // NEW: Generate unique session ID for fresh chat
            document.getElementById('chat-input').disabled = false;
            document.getElementById('chat-btn').disabled = false;
            document.getElementById('chat-messages').innerHTML = '<div class="alert success">✓ Chart selected! Start a fresh conversation.</div>';
            loadUsers();
        }
        
        // Send Chat Message
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        async function sendMessage() {
            if (!selectedUserId) {
                document.getElementById('chat-alert').innerHTML = '<div class="alert error">Please select a birth chart first!</div>';
                return;
            }
            
            const input = document.getElementById('chat-input');
            const messages = document.getElementById('chat-messages');
            const btn = document.getElementById('chat-btn');
            const query = input.value.trim();
            
            if (!query) return;
            
            // Add user message
            messages.innerHTML += '<div class="message user">' + query + '</div>';
            input.value = '';
            messages.scrollTop = messages.scrollHeight;
            
            btn.disabled = true;
            btn.innerHTML = '<span class="loading"></span>';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: selectedUserId,
                        query: query,
                        session_id: currentSessionId,  // NEW: Send session ID for conversation isolation
                        character_id: selectedCharacter  // NEW: Send selected character
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Split response by ||| separator for multiple messages
                    const responses = result.response.split('|||').map(r => r.trim()).filter(r => r);
                    responses.forEach(resp => {
                        messages.innerHTML += '<div class="message assistant">' + resp + '</div>';
                    });
                } else {
                    messages.innerHTML += '<div class="message assistant" style="background:#f8d7da; color:#721c24;">Error: ' + result.error + '</div>';
                }
            } catch (error) {
                messages.innerHTML += '<div class="message assistant" style="background:#f8d7da; color:#721c24;">Failed to get response. Please try again.</div>';
            }
            
            messages.scrollTop = messages.scrollHeight;
            btn.disabled = false;
            btn.textContent = 'Send';
        }

        // Initialize: Load characters when page loads
        window.addEventListener('DOMContentLoaded', () => {
            loadCharacters();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Welcome page with API documentation"""
    return render_template_string(HOME_HTML)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ASTRA Vedic Astrology API",
        "version": "1.0.0"
    })

@app.route('/api/users', methods=['GET'])
def list_users():
    """List all users - DEPRECATED (DB removed)"""
    return jsonify({
        "success": False,
        "error": "Database removed. Use /api/v1/chat with birth data in request."
    }), 410  # Gone

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user - DEPRECATED (DB removed)"""
    return jsonify({
        "success": False,
        "error": "Database removed. Use /api/v1/chat with birth data in request."
    }), 410  # Gone

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details - DEPRECATED (DB removed)"""
    return jsonify({
        "success": False,
        "error": "Database removed. Use /api/v1/chat with birth data in request."
    }), 410  # Gone

@app.route('/api/characters', methods=['GET'])
def get_characters():
    """Get all available character personas"""
    try:
        from src.utils.characters import get_all_characters

        characters = get_all_characters()

        return jsonify({
            "success": True,
            "characters": characters
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with Astra - DEPRECATED (DB removed). Use /api/v1/chat instead."""
    return jsonify({
        "success": False,
        "error": "Database removed. Use /api/v1/chat with birth data in request. See /docs/ASTROVOICE_API.md for details."
    }), 410  # Gone

# ==================================================================
# ASTROVOICE INTEGRATION API (v1)
# ==================================================================

# API Key for authentication (set in environment variable)
ASTROVOICE_API_KEY = os.environ.get('ASTROVOICE_API_KEY', None)

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth if no API key is configured
        if not ASTROVOICE_API_KEY:
            return f(*args, **kwargs)

        # Check for API key in header
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')

        if not api_key or api_key != ASTROVOICE_API_KEY:
            return jsonify({
                "success": False,
                "error": "Invalid or missing API key"
            }), 401

        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/v1/health', methods=['GET'])
def health_check_v1():
    """
    Health Check Endpoint

    Returns server status and available services.

    Response:
    {
        "success": true,
        "status": "healthy",
        "services": {
            "llm": "available",
            "astro_engine": "ready"
        },
        "version": "1.0.0"
    }
    """
    try:
        # Check LLM availability
        llm_status = "available" if llm and llm.client else "unavailable"

        # Check astro engine
        astro_status = "ready" if astro else "unavailable"

        return jsonify({
            "success": True,
            "status": "healthy",
            "services": {
                "llm": llm_status,
                "astro_engine": astro_status
            },
            "version": "1.0.0"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500


@app.route('/api/v1/characters', methods=['GET'])
@require_api_key
def get_characters_v1():
    """
    Get Available Characters

    Returns list of all available astrologer characters.

    Response:
    {
        "success": true,
        "characters": [
            {
                "id": "general",
                "name": "Astra",
                "specialty": "General",
                "description": "General Vedic Astrology consultant"
            },
            ...
        ]
    }
    """
    try:
        from src.utils.characters import get_all_characters
        characters_dict = get_all_characters()

        # Convert to list format for easier consumption
        characters_list = []
        for char_id, char_info in characters_dict.items():
            characters_list.append({
                "id": char_id,
                "name": char_info.get("name", "Unknown"),
                "specialty": char_info.get("description", "General"),
                "description": f"{char_info.get('name', 'Unknown')} - {char_info.get('description', 'General')} specialist"
            })

        return jsonify({
            "success": True,
            "characters": characters_list,
            "count": len(characters_list)
        })
    except Exception as e:
        logger.error(f"Failed to get characters: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/chat', methods=['POST'])
@require_api_key
def chat_v1():
    """
    AstroVoice Integration Endpoint

    Receives birth data AND character data directly from AstroVoice.

    Request:
    {
        "user_id": 1,                    // Required - for tracking
        "query": "When will I get married?",  // Required - user's question
        "session_id": "session_123",     // Required - conversation tracking

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
        "birth_date": "15/08/1990",      // DD/MM/YYYY
        "birth_time": "14:30",           // HH:MM (24hr)
        "birth_location": "Mumbai, India",
        "latitude": 19.076,
        "longitude": 72.877,
        "timezone": "Asia/Kolkata",
        
        // Preferred Language (Optional, defaults to Hinglish)
        "preferred_language": "Hinglish",  // Options: "Hindi", "English", "Hinglish", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali"

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

        # Validate REQUIRED fields
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

        # Character data from AstroVoice
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
        character_age = character_data.get('age')
        character_experience = character_data.get('experience')
        character_specialty = character_data.get('specialty', 'General Vedic Astrology')
        character_language_style = character_data.get('language_style', 'casual')
        character_about = character_data.get('about', '')

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
        
        # Language preference (optional, defaults to Hinglish)
        preferred_language = data.get('preferred_language', 'Hinglish')

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

        # Add language preference to character data
        character_data_with_lang = character_data.copy()
        character_data_with_lang['preferred_language'] = preferred_language
        
        # Generate response with character data and conversation history
        result = llm.generate_response(
            user_id=user_id,
            user_query=query,
            natal_context=natal_context,
            transit_context=transit_context,
            session_id=session_id,
            character_id=character_id,
            conversation_history=conversation_history,
            character_data=character_data_with_lang  # Pass full character data with language
        )

        response = result['response']

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
    app.run(host='0.0.0.0', port=port, debug=False)
