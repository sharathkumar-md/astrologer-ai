from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import json as json_lib
from database import UserDatabase
from astro_engine import AstroEngine
from llm_bridge import LLMBridge
import config

app = Flask(__name__, static_folder='static')
CORS(app)

# Initialize components
db = UserDatabase(config.DB_NAME)
astro = AstroEngine()
llm = LLMBridge()

# Store user sessions with natal charts
user_sessions = {}

# Serve static files
@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/create-user', methods=['POST'])
def create_user():
    try:
        data = request.json
        name = data.get('name')
        date_str = data.get('date')  # DD/MM/YYYY
        time_str = data.get('time')  # HH:MM
        location = data.get('location')
        
        # Get location coordinates
        location_data = astro.get_location_data(location)
        if not location_data:
            return jsonify({'error': 'Location not found'}), 400
        
        lat, lon, tz_str = location_data
        
        # Parse date and time
        day, month, year = map(int, date_str.split('/'))
        hour, minute = map(int, time_str.split(':'))
        
        # Create natal chart object
        natal_chart = astro.create_natal_chart(name, year, month, day, hour, minute, location, lat, lon, tz_str)
        
        # Serialize chart for storage
        chart_data = astro.get_chart_data(natal_chart)
        
        # Store in database
        user_id = db.add_user(name, date_str, time_str, location, lat, lon, tz_str, json_lib.dumps(chart_data))
        
        # Initialize user session
        user_sessions[user_id] = {
            'name': name,
            'natal_chart': natal_chart,
            'location': location,
            'lat': lat,
            'lon': lon,
            'tz': tz_str,
            'conversation_history': []
        }
        
        return jsonify({
            'user_id': user_id,
            'message': f'✨ Chart created for {name}!'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/load-user/<int:user_id>', methods=['GET'])
def load_user(user_id):
    try:
        user_data = db.get_user(user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Unpack user data tuple
        uid, name, birth_date, birth_time, location, lat, lon, tz_str, chart_json, created_at = user_data
        
        # Recreate natal chart from stored data
        day, month, year = map(int, birth_date.split('/'))
        hour, minute = map(int, birth_time.split(':'))
        
        natal_chart = astro.create_natal_chart(name, year, month, day, hour, minute, location, lat, lon, tz_str)
        
        # Initialize user session
        user_sessions[user_id] = {
            'name': name,
            'natal_chart': natal_chart,
            'location': location,
            'lat': lat,
            'lon': lon,
            'tz': tz_str,
            'conversation_history': []
        }
        
        return jsonify({
            'user_id': user_id,
            'name': name,
            'location': location
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get('user_id')
        message = data.get('message')
        
        if user_id not in user_sessions:
            return jsonify({'error': 'User session not found'}), 404
        
        session = user_sessions[user_id]
        
        # Add user message to history
        session['conversation_history'].append({
            'role': 'user',
            'content': message
        })
        
        # Get AI response
        # Get transit chart for context
        transit_chart = astro.get_transit_chart(session['location'], session['lat'], session['lon'], session['tz'])
        
        response = llm.generate_response(
            session['natal_chart'],
            transit_chart,
            message,
            session['conversation_history']
        )
        
        # Add AI response to history
        session['conversation_history'].append({
            'role': 'assistant',
            'content': response
        })
        
        # Save conversation to database
        db.add_conversation(user_id, message, response)
        
        return jsonify({
            'response': response
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/users', methods=['GET'])
def list_users():
    try:
        users = db.list_users()
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'name': user[1],
                'location': user[2]  # birth_location
            })
        return jsonify({'users': user_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
