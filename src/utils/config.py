import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Model for chat completions
# Supported models with caching: gpt-4o, gpt-4o-mini, o1-preview, o1-mini
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# NOTE: Database configuration removed
# All user/birth data is provided by AstroVoice integration via API requests
# See /docs/ASTROVOICE_API.md for the API documentation
