#!/bin/bash

# Quick start script for local development
# Run this to set up and start the ASTRA web server

echo "🌙 ASTRA - Starting Web Server..."

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Create a .env file with:"
    echo "   GROQ_API_KEY=your_api_key_here"
    echo "   MODEL_NAME=llama-3.1-8b-instant"
    echo ""
    echo "Get your free API key from: https://console.groq.com"
    echo ""
    read -p "Enter your GROQ API Key: " api_key
    echo "GROQ_API_KEY=$api_key" > .env
    echo "MODEL_NAME=llama-3.1-8b-instant" >> .env
    echo "✅ .env file created!"
fi

# Start the server
echo "🚀 Starting Flask server..."
echo "📱 Open your browser at: http://localhost:5000"
echo "⏹️  Press Ctrl+C to stop"
echo ""

python app.py
