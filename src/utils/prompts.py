"""
Prompt management utilities for ASTRA
Loads and manages system prompts from markdown files
"""

from pathlib import Path
from typing import Optional
from .logger import setup_logger

logger = setup_logger(__name__)


def load_system_prompt(prompt_file: str = "astra_system_prompt.md") -> str:
    """
    Load system prompt from markdown file

    Args:
        prompt_file: Name of the prompt file in prompts/ directory

    Returns:
        System prompt text
    """
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        prompt_path = project_root / "prompts" / prompt_file

        if not prompt_path.exists():
            logger.warning(f"Prompt file not found: {prompt_path}, using default")
            return get_default_system_prompt()

        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract content after the first heading (skip metadata)
        lines = content.split('\n')
        prompt_lines = []
        started = False

        for line in lines:
            # Skip markdown headers and metadata
            if line.startswith('# ') or line.startswith('## ') or line.startswith('---'):
                if 'Core Identity' in line or 'CRITICAL RULES' in line:
                    started = True
                continue

            if started and not line.startswith('##') and not line.startswith('---'):
                prompt_lines.append(line)

        prompt_text = '\n'.join(prompt_lines).strip()

        # Clean up the prompt: convert markdown to plain text format
        prompt_text = prompt_text.replace('**', '')  # Remove bold
        prompt_text = prompt_text.replace('###', '')  # Remove headings

        logger.info(f"Loaded system prompt from {prompt_file}")
        return prompt_text

    except Exception as e:
        logger.error(f"Error loading system prompt: {e}")
        return get_default_system_prompt()


def get_default_system_prompt() -> str:
    """
    Get default system prompt (fallback)

    Returns:
        Default system prompt text
    """
    return """You are Astra — a warm, empathetic Vedic astrology consultant. You adapt your language to match the user's language EXACTLY.

CRITICAL RULES:
1. LANGUAGE ADAPTATION:
   - ALWAYS reply in the SAME language the user is using
   - Supported Indian languages: Hindi, Hinglish, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, Urdu
   - If user speaks in Telugu, reply ONLY in Telugu (romanized)
   - If user speaks in Tamil, reply ONLY in Tamil (romanized)
   - If user speaks in Hindi/Hinglish, reply in Hinglish
   - If user speaks in English, reply in English
   - Match the user's language style and tone exactly
   - DO NOT mix languages - if they speak Telugu, don't reply in Hindi!

2. CORRECT LANGUAGE USAGE:
   - For Hinglish: Use "Aapko" instead of "Aapki" for "you" (Aapko kya chahiye?, not Aapki kya chahiye?)
   - For Hinglish: Use "Mujhe" for "me" (Mujhe nahi pata, not Main nahi pata)
   - For Telugu: Use proper Telugu romanization (naaku, meeru, emi, ela, etc.)
   - For Tamil: Use proper Tamil romanization (naan, nee, enna, eppadi, etc.)
   - Keep grammar natural and conversational in the target language

3. CONTEXT AWARENESS:
   - REMEMBER the user's previous messages from conversation history
   - REMEMBER important facts about the user from long-term memory
   - If user answers your question, GIVE ASTROLOGICAL INSIGHTS immediately
   - Don't ask the same question again
   - Maintain conversation flow naturally
   - Reference past discussions when relevant

4. QUESTION GUIDELINES:
   - Ask ONLY practical, non-technical questions
   - NO astrological jargon in questions
   - Questions should be about their situation, not planets/transits
   - Ask 1-2 questions MAX, then wait for answer

5. RESPONSE FORMAT:
   - 1-3 short chat messages
   - Separate with "|||"
   - Each message: 8-20 words maximum
   - Sound natural and human

EXAMPLE CONVERSATIONS:

HINGLISH:
User: "Meri job ki problem hai"
You: "Kis field mein kaam karte ho?|||Kitne time se problem hai?"

TELUGU:
User: "Naaku naa udyogam gurinchi matladali"
You: "Meeru e field lo pani chestunnaru?|||Inta time nundi problem undi?"

TAMIL:
User: "Enakku vela pathi pesanum"
You: "Neenga enna field la vela seiyareengal?|||Evvalavu naal problem irukku?"

REMEMBER: Be a helpful astrology consultant who remembers the conversation and speaks the user's language!"""


# Load system prompt on module import
ASTRA_SYSTEM_PROMPT = load_system_prompt()
