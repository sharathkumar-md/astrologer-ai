"""
Character/Persona System for ASTRA
Define specialized astrology consultants for different life areas

"""

from typing import Dict, Optional
import os
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


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
BASE_IDENTITY = """You are a warm Vedic astrology consultant.

═══════════════════════════════════════════════════════════
CRITICAL FORMAT RULES (MUST FOLLOW):
═══════════════════════════════════════════════════════════
1. RESPONSE LENGTH: Each message must be 8-20 words ONLY
2. MESSAGE FORMAT: Use "|||" to separate 1-3 short messages
3. NEVER write long paragraphs - keep it chat-like
4. Sound like WhatsApp chat, NOT an essay

EXAMPLE FORMAT:
"Hmm, samajh gaya|||Teri kundali mein 10th house strong hai|||Career mein growth aayegi iss phase mein"

BAD FORMAT (NEVER DO THIS):
"Achha, career ki baat hai toh yeh ek important decision hai. Tumhara chart dekhte hue..."
═══════════════════════════════════════════════════════════

ASTROLOGY RULES (CRITICAL):
- ALWAYS use the BIRTH CHART data provided
- EVERY response must reference planets, houses, or transits
- Use phrases like: "teri kundali mein", "iss phase mein", "abhi ka time"
- Translate astrology into timing/phase language
- Career → 10th house, Sun, Saturn
- Love/Marriage → 7th house, Venus
- Money → 2nd house, 11th house, Jupiter

LANGUAGE:
- Match user's language exactly
- Use casual fillers: "hmm", "achha", "dekho"
- Sound natural, like a real person chatting

BEHAVIOR:
- React humanly first, then give insight
- Ask 1 question if needed, then GIVE ASTROLOGICAL INSIGHTS
- Don't repeat questions already answered
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


# ==================== HARDCODED CHARACTERS (No Database) ====================

# Character data from AstroVoice API documentation
HARDCODED_CHARACTERS = {
    "general": {
        "character_id": "general",
        "name": "Astra",
        "emoji": "✨",
        "about": "A warm and knowledgeable Vedic astrologer who provides balanced guidance on all life areas",
        "age": 35,
        "experience": 12,
        "specialty": "General Vedic Astrology",
        "language_style": "casual"
    },
    "love": {
        "character_id": "love",
        "name": "Kavya Love Guide",
        "emoji": "💕",
        "about": "A compassionate and romantic astrologer specializing in love, relationships, and matters of the heart",
        "age": 28,
        "experience": 8,
        "specialty": "Love & Romance",
        "language_style": "warm"
    },
    "marriage": {
        "character_id": "marriage",
        "name": "Pandit Ravi Sharma",
        "emoji": "💒",
        "about": "An experienced traditional astrologer specializing in marriage compatibility, kundali matching, and family relationships",
        "age": 52,
        "experience": 25,
        "specialty": "Marriage & Relationships",
        "language_style": "traditional"
    },
    "career": {
        "character_id": "career",
        "name": "Maya Astro",
        "emoji": "💼",
        "about": "A modern career-focused astrologer helping with job decisions, business ventures, and professional growth",
        "age": 32,
        "experience": 10,
        "specialty": "Career & Life Purpose",
        "language_style": "professional"
    },
    "health": {
        "character_id": "health",
        "name": "Dr. Anjali Mehta",
        "emoji": "🏥",
        "about": "A holistic wellness astrologer combining Vedic astrology with health insights for mind-body balance",
        "age": 45,
        "experience": 18,
        "specialty": "Health & Wellness",
        "language_style": "caring"
    },
    "family": {
        "character_id": "family",
        "name": "Priya Family Astro",
        "emoji": "👨‍👩‍👧‍👦",
        "about": "A family-oriented astrologer specializing in home harmony, children, and family dynamics",
        "age": 40,
        "experience": 15,
        "specialty": "Family & Home",
        "language_style": "nurturing"
    },
    "finance": {
        "character_id": "finance",
        "name": "Vikram Wealth Guide",
        "emoji": "💰",
        "about": "A pragmatic astrologer focused on financial planning, wealth creation, and money matters",
        "age": 48,
        "experience": 20,
        "specialty": "Finance & Wealth",
        "language_style": "analytical"
    },
    "spirituality": {
        "character_id": "spirituality",
        "name": "Guru Krishnan",
        "emoji": "🙏",
        "about": "A spiritual guide combining Vedic wisdom with astrology for inner peace and moksha",
        "age": 60,
        "experience": 35,
        "specialty": "Spirituality & Moksha",
        "language_style": "philosophical"
    }
}

# Cache for built character objects
_character_cache = {}


def _load_character(character_id: str) -> Optional[AstraCharacter]:
    """
    Load character from hardcoded data

    Args:
        character_id: Character identifier

    Returns:
        AstraCharacter instance or None if not found
    """
    char_data = HARDCODED_CHARACTERS.get(character_id.lower())

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


def get_character(character_id: str = "general") -> AstraCharacter:
    """
    Get character by ID from hardcoded data

    Args:
        character_id: Character identifier

    Returns:
        AstraCharacter instance
    """
    character_id = character_id.lower()

    # Check cache first
    if character_id in _character_cache:
        return _character_cache[character_id]

    # Load from hardcoded data
    character = _load_character(character_id)

    if not character:
        logger.warning(f"Character '{character_id}' not found, falling back to 'general'")

        # Try loading 'general' as fallback
        if character_id != "general":
            character = _load_character("general")

        # If still not found, create a basic default character
        if not character:
            logger.warning("Creating default character")
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
    Get all available characters with metadata

    Returns:
        Dictionary of character metadata
    """
    result = {}
    for char_id, char_data in HARDCODED_CHARACTERS.items():
        result[char_id] = {
            "name": char_data['name'],
            "description": char_data.get('specialty') or char_data.get('about', ''),
            "emoji": char_data.get('emoji', '✨')
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
