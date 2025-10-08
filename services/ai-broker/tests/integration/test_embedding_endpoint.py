"""Integration tests for /embedding endpoint"""

from fastapi.testclient import TestClient


class TestEmbeddingEndpoint:
    """Test suite for /embedding endpoint"""

    def test_embedding_endpoint_success(self, client: TestClient, sample_embedding_request):
        """Test successful embedding request"""
        response = client.post("/embedding", json=sample_embedding_request)
        assert response.status_code == 200

    def test_embedding_response_format(self, client: TestClient, sample_embedding_request):
        """Test embedding response has all required fields"""
        response = client.post("/embedding", json=sample_embedding_request)
        data = response.json()

        # Check all required fields are present
        assert "embedding" in data
        assert "model" in data
        assert "dimensions" in data
        assert "correlation_id" in data

        # Validate field types
        assert isinstance(data["embedding"], list)
        assert isinstance(data["model"], str)
        assert isinstance(data["dimensions"], int)
        assert isinstance(data["correlation_id"], str)

    def test_embedding_mock_mode(self, client: TestClient, sample_embedding_request):
        """Test embedding in mock mode"""
        response = client.post("/embedding", json=sample_embedding_request)
        data = response.json()

        # In mock mode, model name should have "(mock)" suffix
        assert "(mock)" in data["model"]
        assert data["dimensions"] == 768  # Standard BERT-like dimension
        assert len(data["embedding"]) == 768

    def test_embedding_vector_properties(self, client: TestClient, sample_embedding_request):
        """Test embedding vector properties"""
        response = client.post("/embedding", json=sample_embedding_request)
        data = response.json()

        # Verify all values are floats
        assert all(isinstance(val, (int, float)) for val in data["embedding"])

        # Verify values are in reasonable range (normalized)
        assert all(-1.0 <= val <= 1.0 for val in data["embedding"])

    def test_embedding_minimal_request(self, client: TestClient):
        """Test embedding with minimal required fields"""
        minimal_request = {"text": "Sample text for embedding"}
        response = client.post("/embedding", json=minimal_request)
        assert response.status_code == 200

    def test_embedding_with_custom_model(self, client: TestClient):
        """Test embedding with custom model"""
        request = {"text": "Test text", "model": "textembedding-gecko-multilingual"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_with_metadata(self, client: TestClient):
        """Test embedding with custom metadata"""
        request = {"text": "Test text", "metadata": {"source": "test_suite", "batch": "batch_1"}}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_missing_text(self, client: TestClient):
        """Test embedding without text (should fail validation)"""
        request = {"model": "textembedding-gecko"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 422  # Validation error

    def test_embedding_empty_text(self, client: TestClient):
        """Test embedding with empty text"""
        request = {"text": ""}
        response = client.post("/embedding", json=request)
        # Should succeed (service should handle empty text)
        assert response.status_code == 200

    def test_embedding_long_text(self, client: TestClient):
        """Test embedding with very long text"""
        long_text = "word " * 1000  # 1000 words
        request = {"text": long_text}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_special_characters(self, client: TestClient):
        """Test embedding with special characters"""
        request = {"text": "Special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/~`"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_unicode_text(self, client: TestClient):
        """Test embedding with Unicode characters"""
        request = {"text": "Hello 世界 🌍 Привет مرحبا"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_multiline_text(self, client: TestClient):
        """Test embedding with multiline text"""
        request = {"text": "Line 1\nLine 2\nLine 3"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_deterministic(self, client: TestClient):
        """Test that same text produces same embedding"""
        request = {"text": "Consistent text for testing"}

        response1 = client.post("/embedding", json=request)
        response2 = client.post("/embedding", json=request)

        data1 = response1.json()
        data2 = response2.json()

        # Same input should produce same embedding
        assert data1["embedding"] == data2["embedding"]

    def test_embedding_different_texts(self, client: TestClient):
        """Test that different texts produce different embeddings"""
        request1 = {"text": "First text"}
        request2 = {"text": "Second text"}

        response1 = client.post("/embedding", json=request1)
        response2 = client.post("/embedding", json=request2)

        data1 = response1.json()
        data2 = response2.json()

        # Different inputs should produce different embeddings
        assert data1["embedding"] != data2["embedding"]

    def test_embedding_dimensions_match_length(self, client: TestClient):
        """Test that dimensions field matches embedding vector length"""
        request = {"text": "Test text"}
        response = client.post("/embedding", json=request)
        data = response.json()

        assert data["dimensions"] == len(data["embedding"])

    def test_embedding_correlation_id_present(self, client: TestClient):
        """Test that correlation_id is present in response"""
        request = {"text": "test"}
        response = client.post("/embedding", json=request)
        data = response.json()
        assert len(data["correlation_id"]) > 0

    def test_embedding_content_type(self, client: TestClient):
        """Test that response has correct content type"""
        request = {"text": "test"}
        response = client.post("/embedding", json=request)
        assert response.headers["content-type"] == "application/json"

    def test_embedding_invalid_json(self, client: TestClient):
        """Test embedding with invalid JSON"""
        response = client.post(
            "/embedding", data="not valid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_embedding_different_models(self, client: TestClient):
        """Test embedding with different model names"""
        models = [
            "textembedding-gecko",
            "textembedding-gecko-multilingual",
            "custom-embedding-model",
        ]
        for model in models:
            request = {"text": "test", "model": model}
            response = client.post("/embedding", json=request)
            assert response.status_code == 200

    def test_embedding_concurrent_requests(self, client: TestClient):
        """Test multiple concurrent embedding requests"""
        import concurrent.futures

        def make_request(text):
            return client.post("/embedding", json={"text": text})

        texts = [f"Test text {i}" for i in range(5)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, text) for text in texts]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(r.status_code == 200 for r in responses)

    def test_embedding_batch_consistency(self, client: TestClient):
        """Test embedding consistency across batch of requests"""
        text = "Consistent test text"
        responses = []

        for _ in range(3):
            response = client.post("/embedding", json={"text": text})
            responses.append(response.json())

        # All responses should have same embedding for same text
        first_embedding = responses[0]["embedding"]
        assert all(r["embedding"] == first_embedding for r in responses)


class TestEmbeddingWithAuth:
    """Test embedding endpoint with authentication scenarios"""

    def test_embedding_with_auth_headers(self, client: TestClient, auth_headers):
        """Test embedding with authentication headers"""
        request = {"text": "test"}
        response = client.post("/embedding", json=request, headers=auth_headers)
        assert response.status_code == 200

    def test_embedding_without_auth_when_not_required(self, client: TestClient):
        """Test embedding works without auth when REQUIRE_AUTH is false"""
        request = {"text": "test"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200


class TestEmbeddingEdgeCases:
    """Test embedding endpoint edge cases"""

    def test_embedding_with_only_spaces(self, client: TestClient):
        """Test embedding with text containing only spaces"""
        request = {"text": "     "}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_with_tabs_and_newlines(self, client: TestClient):
        """Test embedding with tabs and newlines"""
        request = {"text": "\t\n\r"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_with_numbers(self, client: TestClient):
        """Test embedding with numeric text"""
        request = {"text": "12345 67890"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_with_code(self, client: TestClient):
        """Test embedding with code snippet"""
        request = {"text": "def hello(): print('world')"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_with_html(self, client: TestClient):
        """Test embedding with HTML content"""
        request = {"text": "<div>Hello <strong>world</strong></div>"}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200

    def test_embedding_with_json_string(self, client: TestClient):
        """Test embedding with JSON string content"""
        request = {"text": '{"key": "value", "number": 42}'}
        response = client.post("/embedding", json=request)
        assert response.status_code == 200
