# ASTRA API - Render Deployment

Test deployment for ASTRA Vedic Astrology API.

## Endpoints

### Health Check
```
GET /health
```

### Get Characters
```
GET /api/v1/characters
```

### Get Planet Remedies
```
GET /api/v1/remedies/saturn
GET /api/v1/remedies  (all remedies)
```

### Chat (Main Endpoint) - AstroVoice Format
```
POST /api/v1/chat
Content-Type: application/json

{
    "user_id": 1,
    "query": "When will I get married?",
    "session_id": "session_123",

    "character": {
        "id": "marriage",
        "name": "Pandit Ravi Sharma",
        "age": 52,
        "experience": 25,
        "specialty": "Marriage & Relationships",
        "language_style": "traditional",
        "about": "An experienced traditional astrologer"
    },

    "name": "Rahul",
    "birth_date": "15/08/1990",
    "birth_time": "14:30",
    "birth_location": "Mumbai, India",
    "latitude": 19.076,
    "longitude": 72.877,
    "timezone": "Asia/Kolkata",

    "conversation_history": []
}

Response:
{
    "success": true,
    "response": "Achha Rahul, teri kundali mein...",
    "character": {
        "id": "marriage",
        "name": "Pandit Ravi Sharma"
    },
    "session_id": "session_123"
}
```

## Character IDs
- `general` - Astra (General)
- `love` - Kavya Love Guide
- `marriage` - Pandit Ravi Sharma
- `career` - Maya Astro
- `health` - Dr. Anjali Mehta
- `family` - Priya Family Astro
- `finance` - Vikram Wealth Guide
- `spirituality` - Guru Krishnan

## Test with cURL

```bash
# Health check
curl https://YOUR-APP.onrender.com/health

# Get characters
curl https://YOUR-APP.onrender.com/api/v1/characters

# Chat
curl -X POST https://YOUR-APP.onrender.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "query": "meri career kaisi rahegi?",
    "session_id": "test_123",
    "character_id": "career",
    "name": "Test User",
    "birth_date": "15/08/1990",
    "birth_time": "14:30",
    "birth_location": "Mumbai, India",
    "latitude": 19.076,
    "longitude": 72.877,
    "timezone": "Asia/Kolkata"
  }'
```

## Deploy to Render

1. Push to GitHub
2. Go to https://render.com
3. New > Web Service
4. Connect GitHub repo
5. Settings:
   - Root Directory: `.` (root)
   - Build Command: `pip install -r render_deploy/requirements.txt`
   - Start Command: `cd render_deploy && gunicorn app:app --bind 0.0.0.0:$PORT`
6. Environment Variables:
   - `OPENAI_API_KEY` = your key
   - `ASTRA_API_KEY` = optional auth key
7. Deploy!

## Local Testing

```bash
cd render_deploy
pip install -r requirements.txt
python app.py
```

Then visit: http://localhost:5000
