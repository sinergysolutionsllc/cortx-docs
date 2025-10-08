"""Pytest configuration and fixtures for AI Broker tests"""

import os
from typing import Any, Dict, Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables"""
    os.environ["REQUIRE_AUTH"] = "false"
    os.environ["VERTEX_PROJECT_ID"] = ""  # Force mock mode
    os.environ["LOG_LEVEL"] = "ERROR"  # Reduce noise in tests
    yield
    # Cleanup after all tests
    if "VERTEX_PROJECT_ID" in os.environ:
        del os.environ["VERTEX_PROJECT_ID"]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create FastAPI test client"""
    # Import app after environment is set up
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Generate mock auth headers for testing"""
    return {
        "Authorization": "Bearer test-token",
        "X-Tenant-ID": "test-tenant",
        "X-User-ID": "test-user",
    }


@pytest.fixture
def mock_vertex_completion():
    """Mock Vertex AI completion response"""
    mock_response = Mock()
    mock_response.text = "This is a mocked Vertex AI response."
    return mock_response


@pytest.fixture
def mock_vertex_embedding():
    """Mock Vertex AI embedding response"""
    mock_embedding = Mock()
    mock_embedding.values = [0.1] * 768  # 768-dimensional embedding
    return [mock_embedding]


@pytest.fixture
def sample_completion_request() -> Dict[str, Any]:
    """Sample completion request payload"""
    return {
        "prompt": "What is the capital of France?",
        "model": "gemini-pro",
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False,
    }


@pytest.fixture
def sample_embedding_request() -> Dict[str, Any]:
    """Sample embedding request payload"""
    return {
        "text": "This is a test sentence for embedding generation.",
        "model": "textembedding-gecko",
    }


@pytest.fixture
def mock_correlation_id(monkeypatch):
    """Mock correlation ID in request state"""

    def mock_get_correlation_id(request):
        if not hasattr(request.state, "correlation_id"):
            request.state.correlation_id = "test-correlation-id-12345"
        return request.state.correlation_id

    return "test-correlation-id-12345"


@pytest.fixture
def vertex_available_env():
    """Temporarily set Vertex AI as available"""
    original = os.environ.get("VERTEX_PROJECT_ID")
    os.environ["VERTEX_PROJECT_ID"] = "test-project-123"
    yield
    if original:
        os.environ["VERTEX_PROJECT_ID"] = original
    elif "VERTEX_PROJECT_ID" in os.environ:
        del os.environ["VERTEX_PROJECT_ID"]


@pytest.fixture
def mock_generative_model():
    """Mock Vertex AI GenerativeModel"""
    with patch("app.main.GenerativeModel") as mock:
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.text = "Mocked Vertex AI response"
        mock_instance.generate_content.return_value = mock_response
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_text_embedding_model():
    """Mock Vertex AI TextEmbeddingModel"""
    with patch("app.main.TextEmbeddingModel") as mock:
        mock_instance = Mock()
        mock_embedding = Mock()
        mock_embedding.values = [0.1] * 768
        mock_instance.get_embeddings.return_value = [mock_embedding]
        mock.from_pretrained.return_value = mock_instance
        yield mock


@pytest.fixture
def disable_auth():
    """Disable authentication for specific tests"""
    original = os.environ.get("REQUIRE_AUTH")
    os.environ["REQUIRE_AUTH"] = "false"
    yield
    if original:
        os.environ["REQUIRE_AUTH"] = original
    elif "REQUIRE_AUTH" in os.environ:
        del os.environ["REQUIRE_AUTH"]


@pytest.fixture
def enable_auth():
    """Enable authentication for specific tests"""
    original = os.environ.get("REQUIRE_AUTH")
    os.environ["REQUIRE_AUTH"] = "true"
    yield
    if original:
        os.environ["REQUIRE_AUTH"] = original
    else:
        os.environ["REQUIRE_AUTH"] = "false"
