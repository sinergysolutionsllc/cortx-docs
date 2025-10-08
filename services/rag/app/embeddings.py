"""
Embedding generation service using Sentence Transformers.

Uses all-MiniLM-L6-v2 model for generating 384-dimensional embeddings.
This model provides a good balance of speed and quality for semantic search.
"""

import logging
import os
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

# Global model instance (loaded once at startup)
_model: Optional[SentenceTransformer] = None


def load_model() -> SentenceTransformer:
    """
    Load the sentence transformer model.

    Loads model on first call and caches it for subsequent calls.
    Model is loaded to CPU by default; set CUDA_VISIBLE_DEVICES for GPU.
    """
    global _model

    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        try:
            _model = SentenceTransformer(MODEL_NAME)
            logger.info(f"✅ Model loaded successfully (dim={EMBEDDING_DIM})")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise

    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Input text to embed

    Returns:
        List of floats representing the embedding vector (384 dimensions)
    """
    model = load_model()

    try:
        # Encode text to embedding
        embedding = model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2 normalization for cosine similarity
        )

        # Convert numpy array to list
        return embedding.tolist()

    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def generate_embeddings_batch(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Generate embeddings for multiple texts (more efficient than one-by-one).

    Args:
        texts: List of input texts to embed
        batch_size: Number of texts to process at once (default: 32)

    Returns:
        List of embedding vectors, one per input text
    """
    model = load_model()

    try:
        # Encode texts in batches for efficiency
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,  # Show progress for large batches
        )

        # Convert numpy arrays to lists
        return [emb.tolist() for emb in embeddings]

    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}")
        raise


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        Cosine similarity score (0 to 1, where 1 is identical)
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)

    # Normalize vectors (if not already normalized)
    v1_norm = v1 / np.linalg.norm(v1)
    v2_norm = v2 / np.linalg.norm(v2)

    # Compute dot product (cosine similarity for normalized vectors)
    similarity = np.dot(v1_norm, v2_norm)

    return float(similarity)


def preload_model() -> None:
    """
    Preload model at application startup.

    Call this in the FastAPI lifespan to avoid latency on first request.
    """
    try:
        load_model()
        logger.info("Embedding model preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload model: {e}")
        # Don't raise - allow app to start even if model fails to load
