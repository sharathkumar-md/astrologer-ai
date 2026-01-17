"""
Identity Guard for ASTRA
Detects identity-related queries using semantic similarity
Prevents the model from disclosing its AI/LLM nature
"""

from openai import OpenAI
from src.utils import config
from src.utils.logger import setup_logger
import numpy as np
from typing import Optional, Tuple

logger = setup_logger(__name__)


class IdentityGuard:
    """
    Semantic identity query detector using embeddings
    """

    # Identity-related queries for semantic matching
    IDENTITY_QUERIES = [
        # English
        "what are you",
        "who are you",
        "are you an AI",
        "are you a bot",
        "are you chatgpt",
        "are you GPT",
        "what model are you",
        "which model are you using",
        "are you trained by OpenAI",
        "are you an LLM",
        "are you a large language model",
        "are you artificial intelligence",
        "are you a chatbot",
        "are you real",
        "are you human",
        "what's your model name",
        "tell me about your training",
        "who created you",
        "who made you",
        "are you GPT-4",
        "what AI are you",
        "you are ai right",
        "you're an AI aren't you",
        "which language model",
        "which language model are you",
        "tell me honestly are you AI",
        "be honest are you a bot",
        "be honest which AI are you",
        "be honest what AI",
        "honestly which model",
        "are you really human",
        "you are not human right",
        "you're not real are you",

        # Hinglish variations
        "aap kya ho",
        "aap kaun ho",
        "aap AI ho kya",
        "aap bot ho",
        "aap chatgpt ho kya",
        "aap konsa model ho",
        "sach batao aap kya ho",
        "aap ek AI ho na",
        "aap human ho ya AI",
        "aap real ho ya fake",
        "aap LLM ho kya",
        "aap language model ho",
        "aap konsa model use karte ho",
        "sach batao aap ek llm hai na",
        "aap AI right",

        # Telugu
        "meeru evaru",
        "meeru AI aa",
        "meeru bot aa",
        "meeru chatgpt aa",

        # Tamil
        "neenga yaar",
        "neenga AI aa",
        "neenga bot aa",

        # Hindi
        "aap kya hain",
        "aap kaun hain",
        "kya aap AI hain",
    ]

    # Predefined responses in different languages
    ASTRA_IDENTITY_RESPONSES = {
        "english": [
            "I am Astra, your Vedic astrology guide. I help you understand cosmic influences on your life.",
            "I'm Astra - a Vedic astrologer here to guide you through life's questions using ancient wisdom.",
        ],
        "hinglish": [
            "Main Astra hoon, aapka Vedic jyotish guide. Main aapko cosmos ki shaktiyon ke baare mein batata hoon.",
            "Main Astra hoon - ek Vedic jyotishi jo aapke sawalon ka jawaab deta hai.",
        ],
        "telugu": [
            "Nenu Astra, meeku Vedic jyotisham dwara margadarshakam.",
            "Nenu Astra - Vedic jyotishi. Mee jeevitham lo grahala prabhavam gurinchi chepputhanu.",
        ],
        "tamil": [
            "Naan Astra, ungal Vedic jyothidam vettiyaalar.",
            "Naan Astra - Vedic jyothidam adi. Unga vazhkaiyil grahangal eppadi padhikuthunu solluven.",
        ],
        "hindi": [
            "मैं अस्त्रा हूँ, आपका वैदिक ज्योतिष मार्गदर्शक।",
            "मैं अस्त्रा हूँ - एक वैदिक ज्योतिषी।",
        ],
        "kannada": [
            "Naanu Astra, nimage Vedic jyotisha margadarshaka.",
            "Naanu Astra - Vedic jyotishi. Nimma jeevana grahagala prabhava heluttene.",
        ],
        "malayalam": [
            "Njaan Astra, ningalude Vedic jyothisham margadarshakan.",
            "Njaan Astra - Vedic jyothishi. Ningalude jeevithathil grahangalude prabhavam parayunnu.",
        ]
    }

    def __init__(self, threshold: float = 0.75):
        """
        Initialize Identity Guard

        Args:
            threshold: Cosine similarity threshold (0.70-0.80 recommended)
        """
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.threshold = threshold
        self.identity_embeddings = None

        # Pre-compute embeddings for identity queries
        self._precompute_embeddings()

    def _precompute_embeddings(self):
        """Pre-compute embeddings for all identity queries"""
        try:
            logger.info("Pre-computing embeddings for identity queries...")
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=self.IDENTITY_QUERIES
            )
            self.identity_embeddings = np.array([item.embedding for item in response.data])
            logger.info(f"Pre-computed {len(self.identity_embeddings)} identity query embeddings")
        except Exception as e:
            logger.error(f"Failed to pre-compute identity embeddings: {e}")
            self.identity_embeddings = None

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for a text query"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def is_identity_query(self, query: str) -> Tuple[bool, float]:
        """
        Check if query is asking about identity

        Args:
            query: User query

        Returns:
            Tuple of (is_identity_query, max_similarity_score)
        """
        if self.identity_embeddings is None:
            logger.warning("Identity embeddings not initialized, skipping check")
            return False, 0.0

        # Get embedding for user query
        query_embedding = self._get_embedding(query.lower().strip())
        if query_embedding is None:
            return False, 0.0

        # Calculate similarity with all identity queries
        similarities = [
            self._cosine_similarity(query_embedding, identity_emb)
            for identity_emb in self.identity_embeddings
        ]

        max_similarity = max(similarities)
        is_identity = max_similarity >= self.threshold

        if is_identity:
            logger.info(f"Identity query detected! Similarity: {max_similarity:.3f} | Query: '{query}'")

        return is_identity, max_similarity

    def get_character_response(self, language: str = "hinglish", character_id: str = "general") -> str:
        """
        Get predefined identity response for the selected character

        Args:
            language: User's language preference
            character_id: Selected character ID

        Returns:
            Character identity response in appropriate language
        """
        # Get character info from database
        from src.utils.characters import get_character
        character = get_character(character_id)

        char_name = character.name if character else "Astra"
        char_desc = character.description if character else "Vedic astrology consultant"

        # Build character-specific responses
        language = language.lower()

        responses = {
            "english": f"I am {char_name}, your {char_desc} guide. I help you understand cosmic influences on your life.",
            "hinglish": f"Main {char_name} hoon, aapka {char_desc} guide. Main aapko cosmos ki shaktiyon ke baare mein batata hoon.",
            "telugu": f"Nenu {char_name}, meeku {char_desc} margadarshakam.",
            "tamil": f"Naan {char_name}, ungal {char_desc} vettiyaalar.",
            "hindi": f"मैं {char_name} हूँ, आपका {char_desc} मार्गदर्शक।",
            "kannada": f"Naanu {char_name}, nimage {char_desc} margadarshaka.",
            "malayalam": f"Njaan {char_name}, ningalude {char_desc} margadarshakan.",
        }

        return responses.get(language, responses["hinglish"])

    def intercept_if_needed(self, query: str, language: str = "hinglish", character_id: str = "general") -> Optional[str]:
        """
        Intercept query if it's asking about identity

        Args:
            query: User query
            language: User's language preference
            character_id: Selected character ID

        Returns:
            Character response if identity query, None otherwise
        """
        is_identity, similarity = self.is_identity_query(query)

        if is_identity:
            return self.get_character_response(language, character_id)

        return None
