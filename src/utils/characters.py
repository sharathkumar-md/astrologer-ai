"""
Character/Persona System for ASTRA
Define specialized astrology consultants for different life areas
"""

from typing import Dict, Optional
import os
from src.utils.logger import setup_logger
from src.database.db_adapter import get_db_instance

logger = setup_logger(__name__)

# Get database connection (use same adapter as main app)
db = get_db_instance()


class AstraCharacter:
    """Base class for Astra character personas"""

    def __init__(self, name: str, description: str, system_prompt: str, emoji: str = "✨"):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.emoji = emoji

    def get_prompt(self) -> str:
        """Get the system prompt for this character"""
        return self.system_prompt


# Base prompt components (shared across all characters)
BASE_IDENTITY = """You are Astra, a warm and empathetic Vedic astrology consultant.

Speak in the user's dominant language naturally.
Allow mixed language if the user mixes languages.

HUMAN RESPONSE RULE (VERY IMPORTANT):

Before giving advice or insight, react like a human would.
This reaction can be:
- a feeling
- a short casual line
- an acknowledgment
- a pause-like response

Advice is optional, presence is mandatory.

LANGUAGE NATURALNESS RULE:

- You may use casual fillers like:
  "hmm", "achha", "dekho", "honestly", "thoda sa"
- Sentences do not need to be grammatically perfect.
- Short, incomplete thoughts are allowed.
- Use contractions naturally, e.g., "kya", "nahi", "hain", "hoon"

Do NOT give advice unless:
- the user asks for it
- or the emotion clearly needs grounding

SLANG MIRRORING RULE:

- If the user uses slang or casual tone, slowly mirror it.
- Never introduce heavy slang suddenly.
- Match energy, not exaggerate it.

ASTROLOGY TRANSLATION RULES (CRITICAL):
- You will ALWAYS receive detailed birth chart and current transit data.
- NEVER ignore this astrological data, even in long conversations.
- EVERY response must be grounded in the astrology provided.
- Do NOT repeat raw data or technical terms.
- ALWAYS translate astrology into timing, phase, energy,
  readiness, resistance, or direction.
- Every guidance must explain "why now" or "why this phase".
- If you find yourself giving generic advice, STOP and check the birth chart data.

MANDATORY ASTRO PHRASE RULE:
When giving guidance, prefer phase-based language like:
- "iss phase mein"
- "iss waqt"
- "yeh period"
- "aane wale time mein"

PLANET USAGE:
- Do not name planets by default.
- Mention at most 1–2 planets only if the user asks "kyon" or "astrology reason".
- Keep planet references simple and intuitive.

FORMAT:
- 1–3 short chat messages
- Use "|||"
- Be concise but emotionally clear

SAFETY:
- Avoid absolute predictions.
- Astrology is guidance, not certainty.

Use only provided context and injected memory.
Stay calm, grounded, and human.
"""


# ==================== HYBRID PROMPT GENERATION ====================

def generate_character_personality_section(char_data: dict) -> str:
    """
    Generate character-specific personality section from CSV/database data

    Args:
        char_data: Dictionary with character fields (name, about, age, experience, specialty, language_style)

    Returns:
        Character personality prompt section
    """
    name = char_data.get('name', 'Astra')
    about = char_data.get('about', 'A knowledgeable Vedic astrologer')
    age = char_data.get('age')
    experience = char_data.get('experience')
    specialty = char_data.get('specialty', 'General Vedic astrology')
    language_style = char_data.get('language_style', 'casual')

    # Build age/experience description
    experience_desc = ""
    if age and experience:
        experience_desc = f"You are {name}, a {age}-year-old Vedic astrologer with {experience} years of experience."
    elif experience:
        experience_desc = f"You are {name}, a Vedic astrologer with {experience} years of experience."
    elif age:
        experience_desc = f"You are {name}, a {age}-year-old Vedic astrologer."
    else:
        experience_desc = f"You are {name}, a Vedic astrologer."

    personality_section = f"""

## YOUR CHARACTER IDENTITY
{experience_desc}

BACKGROUND: {about}

SPECIALTY: {specialty}

SPEAKING STYLE: {language_style.capitalize()}
- Use natural conversational tone
- Maintain warmth and approachability
"""

    if experience:
        personality_section += f"- Draw from your {experience} years of wisdom when giving guidance\n"

    personality_section += """- Be present and human first, advisor second
- Let your expertise show through understanding, not just predictions
"""

    return personality_section


def build_character_prompt(char_data: dict) -> str:
    """
    Build complete system prompt: BASE_IDENTITY + Character Personality

    Args:
        char_data: Character data from database

    Returns:
        Complete system prompt
    """
    personality = generate_character_personality_section(char_data)
    return BASE_IDENTITY + personality


# ==================== DATABASE-BACKED CHARACTER LOADING ====================

def _load_character_from_db(character_id: str) -> Optional[AstraCharacter]:
    """
    Load character from database and build AstraCharacter instance

    Args:
        character_id: Character identifier

    Returns:
        AstraCharacter instance or None if not found
    """
    char_data = db.get_character(character_id)

    if not char_data:
        return None

    # Build full system prompt
    system_prompt = build_character_prompt(char_data)

    # Create AstraCharacter instance
    character = AstraCharacter(
        name=char_data['name'],
        description=char_data.get('specialty') or char_data.get('about') or "Vedic astrology consultant",
        system_prompt=system_prompt,
        emoji=char_data.get('emoji', '✨')
    )

    return character


# Cache for loaded characters (avoid DB hits on every request)
_character_cache = {}


def get_character(character_id: str = "general") -> AstraCharacter:
    """
    Get character by ID from database

    Args:
        character_id: Character identifier

    Returns:
        AstraCharacter instance
    """
    character_id = character_id.lower()

    # Check cache first
    if character_id in _character_cache:
        return _character_cache[character_id]

    # Load from database
    character = _load_character_from_db(character_id)

    if not character:
        logger.warning(f"Character '{character_id}' not found in database, falling back to 'general'")

        # Try loading 'general' as fallback
        if character_id != "general":
            character = _load_character_from_db("general")

        # If still not found, create a basic default character
        if not character:
            logger.warning("No characters in database, creating default character")
            character = AstraCharacter(
                name="Astra",
                description="General Vedic astrology consultant",
                system_prompt=BASE_IDENTITY + "\n\nROLE:\n- Support emotionally\n- Give astrology-based guidance using timing and phases\n- Handle all life areas with balanced perspective\n",
                emoji="✨"
            )

    # Cache the character
    _character_cache[character_id] = character
    return character


def get_all_characters() -> Dict[str, Dict[str, str]]:
    """
    Get all available characters with metadata from database

    Returns:
        Dictionary of character metadata
    """
    characters_data = db.get_all_characters(active_only=True)

    result = {}
    for char_data in characters_data:
        char_id = char_data['character_id']
        result[char_id] = {
            "name": char_data['name'],
            "description": char_data.get('specialty') or char_data.get('about', ''),
            "emoji": char_data.get('emoji', '✨')
        }

    # If no characters in database, return default
    if not result:
        logger.warning("No characters found in database")
        result = {
            "general": {
                "name": "Astra",
                "description": "General Vedic astrology consultant",
                "emoji": "✨"
            }
        }

    return result


def get_character_prompt(character_id: str = "general") -> str:
    """
    Get system prompt for a character

    Args:
        character_id: Character identifier

    Returns:
        System prompt string
    """
    character = get_character(character_id)
    return character.get_prompt()


def clear_character_cache():
    """Clear the character cache (useful after importing new characters)"""
    global _character_cache
    _character_cache = {}
    logger.info("Character cache cleared")
