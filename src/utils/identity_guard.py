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
        "what AI are you"
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

    def __init__(self, threshold: float = 0.80):
        """
        Initialize Identity Guard

        Args:
            threshold: Cosine similarity threshold (0.75-0.85 recommended)
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

    def get_astra_response(self, language: str = "hinglish") -> str:
        """
        Get predefined Astra identity response

        Args:
            language: User's language preference

        Returns:
            Astra identity response in appropriate language
        """
        language = language.lower()
        responses = self.ASTRA_IDENTITY_RESPONSES.get(
            language,
            self.ASTRA_IDENTITY_RESPONSES["hinglish"]
        )

        # Return first response (can randomize if needed)
        return responses[0]

    def intercept_if_needed(self, query: str, language: str = "hinglish") -> Optional[str]:
        """
        Intercept query if it's asking about identity

        Args:
            query: User query
            language: User's language preference

        Returns:
            Astra response if identity query, None otherwise
        """
        is_identity, similarity = self.is_identity_query(query)

        if is_identity:
            return self.get_astra_response(language)

        return None
