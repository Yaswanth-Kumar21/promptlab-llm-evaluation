"""
EmbeddingService — wraps sentence-transformers for local embeddings.

Uses all-MiniLM-L6-v2 (384 dimensions) by default.
- Free, no API key needed
- ~80MB model downloaded once and cached by sentence-transformers
- Fast enough for development (50-200ms per batch)

The model is loaded lazily on first use and cached for the process lifetime.
"""

import numpy as np
from typing import List
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_model = None   # lazy singleton


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        model_name = settings.embedding_model
        logger.info("embedding_model_loading", model=model_name)
        _model = SentenceTransformer(model_name)
        logger.info("embedding_model_ready", model=model_name)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts. Returns a list of float vectors (384-dim).
    Raises on empty input.
    """
    if not texts:
        raise ValueError("embed_texts requires at least one text string.")
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_single(text: str) -> List[float]:
    """Embed a single text string."""
    return embed_texts([text])[0]


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors. Returns value in [-1, 1]."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))
