import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

# NOTE: Database configuration removed
# All user/birth data is provided by AstroVoice integration via API requests
# See /docs/ASTROVOICE_API.md for the API documentation
