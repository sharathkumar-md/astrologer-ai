"""
Main entry point for ASTRA Flask application
Starts the web server with proper logging
"""

import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.dirname(__file__))

from src.api.app import app
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

if __name__ == '__main__':
    port = int(os.environ.get('PORT_BOT', 5000))
    logger.info(f"Starting ASTRA server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
