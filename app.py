from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from database import UserDatabase
from astro_engine import AstroEngine
from llm_bridge import LLMBridge
import config
import os

app = Flask(__name__)
CORS(app)

# Initialize components
db = UserDatabase(config.DB_NAME)
astro = AstroEngine()
llm = LLMBridge()

# Simple HTML template for home page
HOME_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ASTRA - AI Vedic Astrology</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            color: #333;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        h1 {
            text-align: center;
            color: #764ba2;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
        }
        .endpoint {
            background: #f8f9fa;
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .method {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
        }
        .get { background: #28a745; color: white; }
        .post { background: #007bff; color: white; }
        code {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 14px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>✨ ASTRA ✨</h1>
        <p class="subtitle">AI-Powered Vedic Astrology API</p>
        
        <h2>API Endpoints</h2>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/</strong>
            <p>Welcome page with API documentation</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/health</strong>
            <p>Health check endpoint</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/users</strong>
            <p>Create new user birth chart</p>
            <code>{"name": "...", "birth_date": "DD/MM/YYYY", "birth_time": "HH:MM", "location": "..."}</code>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/users</strong>
            <p>List all users</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/users/&lt;user_id&gt;</strong>
            <p>Get user details and birth chart</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/chat</strong>
            <p>Chat with Astra about astrology</p>
            <code>{"user_id": 1, "query": "Tell me about my sun sign"}</code>
        </div>
        
        <div class="footer">
            <p>99Steps</p>
        </div>
    </div>
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
    """List all users"""
    try:
        users = db.list_users()
        return jsonify({
            "success": True,
            "users": [
                {"user_id": uid, "name": name, "birth_date": bd}
                for uid, name, bd in users
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user with birth chart"""
    try:
        data = request.json
        
        # Validate required fields
        required = ['name', 'birth_date', 'birth_time', 'location']
        for field in required:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Get location data
        location_data = astro.get_location_data(data['location'])
        if not location_data:
            return jsonify({
                "success": False,
                "error": f"Location '{data['location']}' not found"
            }), 404
        
        lat, lon, tz_str = location_data
        
        # Parse date and time
        day, month, year = map(int, data['birth_date'].split('/'))
        hour, minute = map(int, data['birth_time'].split(':'))
        
        # Create natal chart
        natal_chart = astro.create_natal_chart(
            data['name'], year, month, day, hour, minute, 
            data['location'], lat, lon, tz_str
        )
        
        chart_data = astro.get_chart_data(natal_chart)
        
        # Save to database
        user_id = db.add_user(
            data['name'], data['birth_date'], data['birth_time'],
            data['location'], lat, lon, tz_str, chart_data
        )
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "message": "Birth chart created successfully",
            "chart_summary": chart_data
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details and birth chart"""
    try:
        user_data = db.get_user(user_id)
        if not user_data:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        import json
        return jsonify({
            "success": True,
            "user": {
                "user_id": user_data[0],
                "name": user_data[1],
                "birth_date": user_data[2],
                "birth_time": user_data[3],
                "birth_location": user_data[4],
                "latitude": user_data[5],
                "longitude": user_data[6],
                "timezone": user_data[7],
                "natal_chart": json.loads(user_data[8]) if user_data[8] else None,
                "created_at": user_data[9]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with Astra about astrology"""
    try:
        data = request.json
        
        # Validate required fields
        if 'user_id' not in data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields: user_id and query"
            }), 400
        
        user_id = data['user_id']
        query = data['query']
        
        # Get user data
        user_data = db.get_user(user_id)
        if not user_data:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Reconstruct natal chart
        import json
        natal_chart_data = json.loads(user_data[8])
        
        # Create natal chart object from stored data
        natal_chart = astro.create_natal_chart(
            user_data[1],  # name
            int(user_data[2].split('/')[2]),  # year
            int(user_data[2].split('/')[1]),  # month
            int(user_data[2].split('/')[0]),  # day
            int(user_data[3].split(':')[0]),  # hour
            int(user_data[3].split(':')[1]),  # minute
            user_data[4],  # location
            user_data[5],  # lat
            user_data[6],  # lon
            user_data[7]   # tz
        )
        
        # Get conversation history
        conversation_history = db.get_conversation_history(user_id, limit=10)
        
        # Get astrological context
        natal_context = astro.format_natal_for_llm(natal_chart)
        transit_chart = astro.create_transit_chart(
            user_data[4], user_data[5], user_data[6], user_data[7]
        )
        transit_context = astro.format_transits_for_llm(transit_chart, natal_chart)
        
        # Generate response
        response = llm.generate_response(
            query, natal_context, transit_context, conversation_history
        )
        
        # Save conversation
        db.add_conversation(user_id, query, response)
        
        return jsonify({
            "success": True,
            "query": query,
            "response": response
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
