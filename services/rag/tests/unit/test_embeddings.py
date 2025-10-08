"""
Unit tests for embedding generation service.

Tests cover:
- Model loading and caching
- Single embedding generation
- Batch embedding generation
- Cosine similarity calculation
- Model preloading
- Error handling
"""

from unittest.mock import patch

import numpy as np
import pytest
from app.embeddings import (
    EMBEDDING_DIM,
    MODEL_NAME,
    cosine_similarity,
    generate_embedding,
    generate_embeddings_batch,
    load_model,
    preload_model,
)


class TestModelLoading:
    """Test model loading and caching."""

    def test_load_model_success(self, mock_embedding_model):
        """Test successful model loading."""
        model = load_model()

        assert model is not None
        assert hasattr(model, "encode")

    def test_load_model_caching(self, mock_embedding_model):
        """Test that model is cached after first load."""
        # Load model twice
        model1 = load_model()
        model2 = load_model()

        # Should be the same instance (cached)
        assert model1 is model2

    def test_load_model_failure(self):
        """Test model loading failure."""
        with patch("app.embeddings.SentenceTransformer", side_effect=Exception("Model not found")):
            # Reset cached model
            import app.embeddings

            app.embeddings._model = None

            with pytest.raises(Exception, match="Model not found"):
                load_model()

    def test_preload_model(self, mock_embedding_model):
        """Test model preloading."""
        # Should not raise exception
        preload_model()

        # Model should be loaded
        model = load_model()
        assert model is not None


class TestGenerateEmbedding:
    """Test single embedding generation."""

    def test_generate_embedding_basic(self, mock_embedding_model):
        """Test generating embedding for single text."""
        text = "This is a test sentence."
        embedding = generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIM
        assert all(isinstance(x, float) for x in embedding)

    def test_generate_embedding_empty(self, mock_embedding_model):
        """Test generating embedding for empty string."""
        embedding = generate_embedding("")

        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIM

    def test_generate_embedding_long_text(self, mock_embedding_model):
        """Test generating embedding for long text."""
        text = "This is a test. " * 1000  # Very long text
        embedding = generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIM

    def test_generate_embedding_special_chars(self, mock_embedding_model):
        """Test generating embedding with special characters."""
        text = "Test with émojis 🎉 and spëcial çhars!"
        embedding = generate_embedding(text)

        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIM

    def test_generate_embedding_normalization(self, mock_embedding_model):
        """Test that embeddings are normalized."""
        text = "Test sentence for normalization."
        embedding = generate_embedding(text)

        # Calculate L2 norm
        norm = np.linalg.norm(embedding)

        # Should be close to 1.0 (normalized)
        assert abs(norm - 1.0) < 0.01

    def test_generate_embedding_deterministic(self, mock_embedding_model):
        """Test that same text produces same embedding."""
        text = "Consistent test text."

        embedding1 = generate_embedding(text)
        embedding2 = generate_embedding(text)

        # Should produce identical embeddings
        np.testing.assert_array_almost_equal(embedding1, embedding2)


class TestGenerateEmbeddingsBatch:
    """Test batch embedding generation."""

    def test_generate_embeddings_batch_basic(self, mock_embedding_model):
        """Test generating embeddings for multiple texts."""
        texts = ["First sentence.", "Second sentence.", "Third sentence."]

        embeddings = generate_embeddings_batch(texts)

        assert len(embeddings) == len(texts)
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(len(emb) == EMBEDDING_DIM for emb in embeddings)

    def test_generate_embeddings_batch_empty_list(self, mock_embedding_model):
        """Test generating embeddings for empty list."""
        embeddings = generate_embeddings_batch([])

        assert len(embeddings) == 0

    def test_generate_embeddings_batch_single(self, mock_embedding_model):
        """Test batch generation with single text."""
        embeddings = generate_embeddings_batch(["Single sentence."])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == EMBEDDING_DIM

    def test_generate_embeddings_batch_large(self, mock_embedding_model):
        """Test batch generation with many texts."""
        texts = [f"Sentence number {i}." for i in range(100)]

        embeddings = generate_embeddings_batch(texts, batch_size=32)

        assert len(embeddings) == len(texts)
        assert all(len(emb) == EMBEDDING_DIM for emb in embeddings)

    def test_generate_embeddings_batch_different_lengths(self, mock_embedding_model):
        """Test batch generation with varying text lengths."""
        texts = [
            "Short.",
            "Medium length sentence here.",
            "This is a much longer sentence with many more words to process.",
        ]

        embeddings = generate_embeddings_batch(texts)

        # All should produce same dimension embeddings
        assert len(embeddings) == len(texts)
        assert all(len(emb) == EMBEDDING_DIM for emb in embeddings)

    def test_generate_embeddings_batch_consistency(self, mock_embedding_model):
        """Test that batch and single generation produce same results."""
        texts = ["Test sentence one.", "Test sentence two."]

        # Generate individually
        single_embeddings = [generate_embedding(text) for text in texts]

        # Generate in batch
        batch_embeddings = generate_embeddings_batch(texts)

        # Should be close (might have minor numerical differences)
        for single, batch in zip(single_embeddings, batch_embeddings):
            np.testing.assert_array_almost_equal(single, batch, decimal=5)


class TestCosineSimilarity:
    """Test cosine similarity calculation."""

    def test_cosine_similarity_identical(self):
        """Test similarity between identical vectors."""
        vec = [1.0, 0.0, 0.0]
        similarity = cosine_similarity(vec, vec)

        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_orthogonal(self):
        """Test similarity between orthogonal vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity) < 0.001  # Should be ~0

    def test_cosine_similarity_opposite(self):
        """Test similarity between opposite vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)

        assert abs(similarity - (-1.0)) < 0.001

    def test_cosine_similarity_partial(self):
        """Test similarity between partially similar vectors."""
        vec1 = [1.0, 1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)

        # Should be between 0 and 1
        assert 0.0 < similarity < 1.0

    def test_cosine_similarity_normalized(self):
        """Test that normalization is handled correctly."""
        # Non-normalized vectors
        vec1 = [3.0, 4.0, 0.0]
        vec2 = [6.0, 8.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)

        # Should be 1.0 (same direction, just different magnitude)
        assert abs(similarity - 1.0) < 0.001

    def test_cosine_similarity_high_dimensional(self, mock_embedding_model):
        """Test similarity with high-dimensional vectors."""
        text1 = "This is the first test sentence."
        text2 = "This is the second test sentence."

        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)

        similarity = cosine_similarity(emb1, emb2)

        # Should be between -1 and 1
        assert -1.0 <= similarity <= 1.0

        # Similar sentences should have high similarity
        assert similarity > 0.5

    def test_cosine_similarity_semantic(self, mock_embedding_model):
        """Test semantic similarity with real embeddings."""
        # Similar meaning
        text1 = "The cat sits on the mat."
        text2 = "A feline rests on the rug."

        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)

        similarity = cosine_similarity(emb1, emb2)

        # Should be reasonably similar (semantic similarity)
        assert similarity > 0.3  # Using lower threshold for mock model


class TestErrorHandling:
    """Test error handling in embedding generation."""

    def test_generate_embedding_model_failure(self):
        """Test handling model failure during embedding generation."""
        with patch("app.embeddings.load_model", side_effect=Exception("Model error")):
            with pytest.raises(Exception):
                generate_embedding("Test text")

    def test_generate_embeddings_batch_model_failure(self):
        """Test handling model failure during batch generation."""
        with patch("app.embeddings.load_model", side_effect=Exception("Model error")):
            with pytest.raises(Exception):
                generate_embeddings_batch(["Test text"])

    def test_preload_model_failure_does_not_raise(self):
        """Test that preload_model doesn't raise exceptions."""
        with patch("app.embeddings.load_model", side_effect=Exception("Model error")):
            # Should not raise - just log error
            preload_model()


class TestEmbeddingProperties:
    """Test mathematical properties of embeddings."""

    def test_embedding_range(self, mock_embedding_model):
        """Test that embedding values are in reasonable range."""
        text = "Test sentence for range check."
        embedding = generate_embedding(text)

        # For normalized embeddings, values should be in [-1, 1]
        assert all(-1.0 <= x <= 1.0 for x in embedding)

    def test_embedding_variability(self, mock_embedding_model):
        """Test that different texts produce different embeddings."""
        text1 = "First unique sentence."
        text2 = "Completely different content."

        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)

        # Embeddings should be different
        assert not np.array_equal(emb1, emb2)

        # But similarity should still be measurable
        similarity = cosine_similarity(emb1, emb2)
        assert -1.0 <= similarity <= 1.0

    def test_batch_embedding_order_preserved(self, mock_embedding_model):
        """Test that batch embedding preserves input order."""
        texts = [f"Sentence {i}" for i in range(10)]

        embeddings = generate_embeddings_batch(texts)

        # Generate individually to compare
        individual = [generate_embedding(t) for t in texts]

        # Order should be preserved
        for i, (batch_emb, ind_emb) in enumerate(zip(embeddings, individual)):
            np.testing.assert_array_almost_equal(batch_emb, ind_emb, decimal=5)


class TestModelConfiguration:
    """Test model configuration and settings."""

    def test_model_name_default(self):
        """Test default model name."""
        assert MODEL_NAME == "all-MiniLM-L6-v2" or "EMBEDDING_MODEL" in MODEL_NAME

    def test_embedding_dimension(self):
        """Test embedding dimension constant."""
        assert EMBEDDING_DIM == 384

    def test_embedding_dimension_matches(self, mock_embedding_model):
        """Test that generated embeddings match expected dimension."""
        embedding = generate_embedding("Test")
        assert len(embedding) == EMBEDDING_DIM
