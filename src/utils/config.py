import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

# Database Configuration
DB_NAME = os.getenv("DB_NAME", "astra_users.db")  # SQLite (fallback)
DATABASE_URL = os.getenv("DATABASE_URL")  # PostgreSQL connection URL from Render
USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "false").lower() == "true"
