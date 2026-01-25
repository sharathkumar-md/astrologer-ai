# ASTRA Render Deployment

This folder contains the production deployment setup for Render.com with **database persistence**.

## Features

✅ **Full API Backend** - Flask REST API with all endpoints
✅ **Frontend Interface** - HTML/CSS/JS chat interface  
✅ **Database Persistence** - SQLite database for conversation history
✅ **Session Management** - Automatic session tracking across conversations
✅ **User Tracking** - Automatic user identification by birth details
✅ **Language Support** - 8 languages with preference saving
✅ **OpenAI Caching** - Automatic cost optimization

## Database Structure

### Tables:
1. **users** - Birth details and user information
2. **conversations** - All Q&A exchanges with session tracking
3. **sessions** - Active session metadata (user, character, language)

### How it works:
- **First message**: Creates user + session, generates session_id
- **Subsequent messages**: Loads history from database automatically
- **Same user**: Recognized by birth details (name + date + time + location)
- **Refresh page**: History preserved in database ✅
- **New browser**: History available with same birth details ✅

## Files

- `app.py` - Main Flask application with database integration
- `database.py` - Simple SQLite database handler
- `static/index.html` - Frontend interface
- `static/style.css` - Responsive styling
- `static/script.js` - API integration with session handling
- `requirements.txt` - Python dependencies (includes python-dotenv!)
- `render.yaml` - Render deployment configuration

## Database Location

- **Development**: `astra_render.db` in render_deploy folder
- **Production (Render)**: Persistent disk volume recommended

## API Endpoints

### `/api/v1/chat/simple` (POST)
Main chat endpoint with database persistence.

**Request:**
```json
{
  "message": "When will I get married?",
  "birth_data": {
    "name": "Sharath",
    "birth_date": "1990-08-15",
    "birth_time": "14:30",
    "birth_location": "Mumbai, India"
  },
  "character_data": {
    "character_name": "marriage",
    "preferred_language": "Hinglish"
  },
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Hmm Sharath, dekho teri kundali|||...",
  "session_id": "abc123def456",
  "user_id": 42
}
```

### `/health` (GET)
Health check with database statistics.

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "services": {
    "llm": "available",
    "astro_engine": "ready",
    "database": "connected"
  },
  "database": {
    "total_users": 15,
    "total_conversations": 247,
    "total_sessions": 38
  }
}
```

## How Session Tracking Works

1. **First Request**: 
   - User sends birth details + message
   - Backend creates user in DB (or finds existing)
   - Generates new session_id
   - Returns session_id to frontend

2. **Subsequent Requests**:
   - Frontend sends same birth details + session_id
   - Backend loads conversation history from DB
   - Appends to LLM context automatically
   - Saves new exchange to DB

3. **Caching Still Works**:
   - user_id used for OpenAI cache identification
   - Same user = cache hit on system prompt + birth chart
   - Saves 60-90% on API costs

## Deployment to Render

1. **Commit changes**:
```bash
git add render_deploy/
git commit -m "Add database persistence to render_deploy"
git push
```

2. **On Render Dashboard**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `cd render_deploy && gunicorn app:app --bind 0.0.0.0:$PORT`

3. **Optional: Add Persistent Disk** (recommended for production):
   - Name: `astra-db-storage`
   - Mount path: `/opt/render/project/src/render_deploy/data`
   - Update database.py: `db_name="data/astra_render.db"`

## Environment Variables (Render)

Required:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional:
- `ASTRA_API_KEY` - API authentication key
- `DEBUG` - Set to "true" for debug mode

## Cost Optimization

The system uses OpenAI prompt caching:
- **Without caching**: ~$0.008 per message
- **With caching**: ~$0.001 per message (87% savings!)
- **Database**: Free (SQLite, no external service needed)

## Testing Locally

```bash
cd render_deploy
python app.py
```

Then open: http://localhost:5000

## Notes

- Database file: `astra_render.db` (auto-created)
- Session expires: Never (stored permanently)
- History limit: Last 20 messages per session
- User matching: Exact match on name + birth details
