# ASTRA - AI Vedic Astrology Bot

A soulful astrology companion that combines Kerykeion's precise astronomical calculations with Llama-3.1-8b-instant's empathetic responses to provide deeply personalized astrological guidance.

## 🌐 Now Available as Web App!

ASTRA now includes a beautiful web interface with responsive design! 

- **Web UI**: Modern chat interface with cosmic theme
- **User Management**: Create and load multiple birth charts
- **Real-time Chat**: Interactive conversation with AI astrologer
- **Mobile-Friendly**: Works on all devices
- **Easy Deploy**: Ready for Render, Heroku, or any cloud platform

📚 **Quick Guides**:
- [QUICK_START.md](QUICK_START.md) - Get running in 5 minutes
- [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) - Full deployment guide
- [DEPLOY.md](DEPLOY.md) - Deploy to Render step-by-step

## Features

- **Natal Chart Generation**: Creates detailed birth charts using Kerykeion with accurate planetary positions
- **Transit Analysis**: Calculates current planetary transits and their aspects to your natal chart
- **AI-Powered Insights**: Uses Llama-3.1-8b-instant via Groq API to generate warm, human-like astrological guidance
- **User Management**: SQLite database stores multiple user charts and conversation history
- **Indian Context**: Optimized for Indian locations with IST timezone support
- **Web & CLI**: Available as both web app and command-line interface

## Quick Start (Web Version)

1. **Get Groq API Key**: Sign up at https://console.groq.com and get your free API key

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file**:
   ```bash
   GROQ_API_KEY=your_api_key_here
   MODEL_NAME=llama-3.1-8b-instant
   ```

4. **Run web server**:
   ```bash
   python app.py
   ```

5. **Open browser**: Visit http://localhost:5000

## Quick Start (CLI Version - Original)

1. **Get Groq API Key**: Sign up at https://console.groq.com and get your free API key

2. **Run the bot**:
   ```
   start.bat
   ```

3. **First time setup**: The script will:
   - Create a virtual environment
   - Install all dependencies (kerykeion, groq, pytz)
   - Ask for your Groq API key (saved for future sessions)
   - Launch the bot

4. **Create your chart**: Enter your birth details:
   - Name
   - Birth date (DD/MM/YYYY)
   - Birth time (HH:MM in 24-hour format)
   - Birth location (city name or coordinates)

5. **Start chatting**: Ask Astra anything about your emotions, life situations, or cosmic guidance

## How It Works

### The Prompt Bridge Architecture

1. **Data Layer (Kerykeion)**: Calculates precise astronomical data
   - Natal chart: planetary positions, signs, houses, degrees
   - Transit chart: current planetary positions
   - Aspects: geometric relationships between planets

2. **Translation Layer (AstroEngine)**: Converts raw data into human-readable context
   - Example: `{"planet": "Mars", "sign": "Leo", "house": 5}` becomes
   - "Mars (your drive and passion) is positioned at 15.3° in Leo, illuminating your 5th house of creativity and joy"

3. **AI Layer (LLM Bridge)**: Combines astrological context with user query
   - System prompt defines Astra's personality (warm, intuitive, empathetic)
   - User context includes natal chart + current transits + emotional query
   - Llama-3.1-8b-instant generates personalized, soulful responses

4. **Storage Layer (SQLite)**: Maintains user data and conversation history

## Project Structure

```
99steps/
├── main.py              - Main bot orchestration and user interface
├── astro_engine.py      - Kerykeion wrapper and astrological calculations
├── llm_bridge.py        - Groq API integration and prompt engineering
├── database.py          - SQLite user and conversation management
├── config.py            - Configuration settings
├── requirements.txt     - Python dependencies
├── start.bat           - One-command launcher
└── README.md           - This file
```

## Location Support

Uses OpenStreetMap's Nominatim geocoding service to automatically find coordinates for any city, town, or address worldwide. Just enter the location name (e.g., "Paris, France" or "Tokyo" or "New York, USA") and the system handles the rest.

## Example Interaction

```
You: I feel lonely today

Astra: I see that Transit Saturn is currently forming a Square with your natal Moon in Cancer. This is a time when emotional walls might feel higher, dear one. Saturn is teaching you about emotional boundaries and self-reliance. Your Moon in the 4th house craves connection and nurturing, but Saturn asks you to find that comfort within first. This loneliness is not abandonment - it's an invitation to become your own sanctuary. Light a candle, make yourself chai, and honor this feeling. The square will pass, but the self-love you build now will remain. 🌙
```

## Requirements

- Python 3.8+
- Internet connection (for Groq API calls)
- Windows OS (uses .bat launcher)

## API Usage

Uses Groq's free tier with Llama-3.1-8b-instant model. Each response consumes ~1000 tokens. Free tier includes generous limits for personal use.

## Database

SQLite database (`astra_users.db`) stores:
- User profiles with birth data
- Natal chart calculations (cached as JSON)
- Full conversation history with timestamps

## Customization

Edit `llm_bridge.py` to modify Astra's personality in the `system_prompt`. Current style: warm, empathetic, Vedic-focused, culturally Indian.

## Troubleshooting

- **"GROQ_API_KEY not found"**: Run `set GROQ_API_KEY=your_key` in terminal before running start.bat
- **Location not found**: Enter coordinates manually when prompted
- **Import errors**: Delete venv folder and run start.bat again to reinstall dependencies

## License

Open source - use freely for personal astrological exploration.
