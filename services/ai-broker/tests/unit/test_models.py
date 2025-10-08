"""Unit tests for Pydantic models"""

import pytest
from app.main import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse
from pydantic import ValidationError


class TestCompletionRequest:
    """Test suite for CompletionRequest model"""

    def test_completion_request_minimal(self):
        """Test CompletionRequest with minimal required fields"""
        request = CompletionRequest(prompt="test prompt")
        assert request.prompt == "test prompt"
        assert request.model == "gemini-pro"  # default
        assert request.temperature == 0.7  # default
        assert request.max_tokens == 1024  # default
        assert request.stream is False  # default

    def test_completion_request_all_fields(self):
        """Test CompletionRequest with all fields"""
        request = CompletionRequest(
            prompt="test prompt",
            model="custom-model",
            temperature=0.9,
            max_tokens=2048,
            stream=True,
            system_prompt="You are a helpful assistant",
            metadata={"key": "value"},
        )
        assert request.prompt == "test prompt"
        assert request.model == "custom-model"
        assert request.temperature == 0.9
        assert request.max_tokens == 2048
        assert request.stream is True
        assert request.system_prompt == "You are a helpful assistant"
        assert request.metadata == {"key": "value"}

    def test_completion_request_temperature_validation_min(self):
        """Test temperature validation - minimum bound"""
        with pytest.raises(ValidationError):
            CompletionRequest(prompt="test", temperature=-0.1)

    def test_completion_request_temperature_validation_max(self):
        """Test temperature validation - maximum bound"""
        with pytest.raises(ValidationError):
            CompletionRequest(prompt="test", temperature=2.1)

    def test_completion_request_temperature_edge_cases(self):
        """Test temperature edge cases (0.0 and 2.0 should be valid)"""
        request1 = CompletionRequest(prompt="test", temperature=0.0)
        assert request1.temperature == 0.0

        request2 = CompletionRequest(prompt="test", temperature=2.0)
        assert request2.temperature == 2.0

    def test_completion_request_max_tokens_validation_min(self):
        """Test max_tokens validation - minimum bound"""
        with pytest.raises(ValidationError):
            CompletionRequest(prompt="test", max_tokens=0)

    def test_completion_request_max_tokens_validation_max(self):
        """Test max_tokens validation - maximum bound"""
        with pytest.raises(ValidationError):
            CompletionRequest(prompt="test", max_tokens=8193)

    def test_completion_request_max_tokens_edge_cases(self):
        """Test max_tokens edge cases (1 and 8192 should be valid)"""
        request1 = CompletionRequest(prompt="test", max_tokens=1)
        assert request1.max_tokens == 1

        request2 = CompletionRequest(prompt="test", max_tokens=8192)
        assert request2.max_tokens == 8192

    def test_completion_request_missing_prompt(self):
        """Test that prompt is required"""
        with pytest.raises(ValidationError):
            CompletionRequest()  # type: ignore


class TestCompletionResponse:
    """Test suite for CompletionResponse model"""

    def test_completion_response_creation(self):
        """Test CompletionResponse creation with all fields"""
        response = CompletionResponse(
            text="Generated text",
            model="gemini-pro",
            tokens_used=150,
            finish_reason="stop",
            correlation_id="corr-123",
        )
        assert response.text == "Generated text"
        assert response.model == "gemini-pro"
        assert response.tokens_used == 150
        assert response.finish_reason == "stop"
        assert response.correlation_id == "corr-123"

    def test_completion_response_missing_fields(self):
        """Test that all fields are required"""
        with pytest.raises(ValidationError):
            CompletionResponse(text="test")  # type: ignore

    def test_completion_response_to_dict(self):
        """Test CompletionResponse serialization"""
        response = CompletionResponse(
            text="test",
            model="gemini-pro",
            tokens_used=100,
            finish_reason="stop",
            correlation_id="corr-123",
        )
        data = response.dict()
        assert data["text"] == "test"
        assert data["model"] == "gemini-pro"
        assert data["tokens_used"] == 100


class TestEmbeddingRequest:
    """Test suite for EmbeddingRequest model"""

    def test_embedding_request_minimal(self):
        """Test EmbeddingRequest with minimal required fields"""
        request = EmbeddingRequest(text="test text")
        assert request.text == "test text"
        assert request.model == "textembedding-gecko"  # default
        assert request.metadata is None

    def test_embedding_request_all_fields(self):
        """Test EmbeddingRequest with all fields"""
        request = EmbeddingRequest(
            text="test text", model="custom-embedding-model", metadata={"source": "test"}
        )
        assert request.text == "test text"
        assert request.model == "custom-embedding-model"
        assert request.metadata == {"source": "test"}

    def test_embedding_request_missing_text(self):
        """Test that text is required"""
        with pytest.raises(ValidationError):
            EmbeddingRequest()  # type: ignore

    def test_embedding_request_empty_text(self):
        """Test that empty text is allowed (model should handle)"""
        request = EmbeddingRequest(text="")
        assert request.text == ""


class TestEmbeddingResponse:
    """Test suite for EmbeddingResponse model"""

    def test_embedding_response_creation(self):
        """Test EmbeddingResponse creation with all fields"""
        embedding = [0.1, 0.2, 0.3, 0.4] * 192  # 768 dimensions
        response = EmbeddingResponse(
            embedding=embedding,
            model="textembedding-gecko",
            dimensions=768,
            correlation_id="corr-123",
        )
        assert len(response.embedding) == 768
        assert response.model == "textembedding-gecko"
        assert response.dimensions == 768
        assert response.correlation_id == "corr-123"

    def test_embedding_response_missing_fields(self):
        """Test that all fields are required"""
        with pytest.raises(ValidationError):
            EmbeddingResponse(embedding=[0.1, 0.2])  # type: ignore

    def test_embedding_response_empty_embedding(self):
        """Test EmbeddingResponse with empty embedding list"""
        response = EmbeddingResponse(
            embedding=[], model="test-model", dimensions=0, correlation_id="corr-123"
        )
        assert len(response.embedding) == 0
        assert response.dimensions == 0

    def test_embedding_response_to_dict(self):
        """Test EmbeddingResponse serialization"""
        response = EmbeddingResponse(
            embedding=[0.1, 0.2, 0.3], model="test-model", dimensions=3, correlation_id="corr-123"
        )
        data = response.dict()
        assert data["embedding"] == [0.1, 0.2, 0.3]
        assert data["dimensions"] == 3


class TestModelValidation:
    """Test edge cases and validation across models"""

    def test_completion_request_json_serialization(self):
        """Test that CompletionRequest can be serialized to JSON"""
        request = CompletionRequest(prompt="test", metadata={"nested": {"key": "value"}})
        json_data = request.json()
        assert "test" in json_data

    def test_completion_response_json_serialization(self):
        """Test that CompletionResponse can be serialized to JSON"""
        response = CompletionResponse(
            text="test",
            model="gemini-pro",
            tokens_used=10,
            finish_reason="stop",
            correlation_id="corr-123",
        )
        json_data = response.json()
        assert "test" in json_data

    def test_embedding_request_json_serialization(self):
        """Test that EmbeddingRequest can be serialized to JSON"""
        request = EmbeddingRequest(text="test")
        json_data = request.json()
        assert "test" in json_data

    def test_embedding_response_json_serialization(self):
        """Test that EmbeddingResponse can be serialized to JSON"""
        response = EmbeddingResponse(
            embedding=[0.1, 0.2], model="test", dimensions=2, correlation_id="corr-123"
        )
        json_data = response.json()
        assert "0.1" in json_data or 0.1 in response.embedding
