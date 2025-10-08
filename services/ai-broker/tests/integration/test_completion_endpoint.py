"""Integration tests for /completion endpoint"""

from fastapi.testclient import TestClient


class TestCompletionEndpoint:
    """Test suite for /completion endpoint"""

    def test_completion_endpoint_success(self, client: TestClient, sample_completion_request):
        """Test successful completion request"""
        response = client.post("/completion", json=sample_completion_request)
        assert response.status_code == 200

    def test_completion_response_format(self, client: TestClient, sample_completion_request):
        """Test completion response has all required fields"""
        response = client.post("/completion", json=sample_completion_request)
        data = response.json()

        # Check all required fields are present
        assert "text" in data
        assert "model" in data
        assert "tokens_used" in data
        assert "finish_reason" in data
        assert "correlation_id" in data

        # Validate field types
        assert isinstance(data["text"], str)
        assert isinstance(data["model"], str)
        assert isinstance(data["tokens_used"], int)
        assert isinstance(data["finish_reason"], str)
        assert isinstance(data["correlation_id"], str)

    def test_completion_mock_mode(self, client: TestClient, sample_completion_request):
        """Test completion in mock mode"""
        response = client.post("/completion", json=sample_completion_request)
        data = response.json()

        # In mock mode, model name should have "(mock)" suffix
        assert "(mock)" in data["model"]
        assert data["finish_reason"] == "mock_complete"
        assert len(data["text"]) > 0

    def test_completion_minimal_request(self, client: TestClient):
        """Test completion with minimal required fields"""
        minimal_request = {"prompt": "What is AI?"}
        response = client.post("/completion", json=minimal_request)
        assert response.status_code == 200

    def test_completion_with_system_prompt(self, client: TestClient):
        """Test completion with system prompt"""
        request = {
            "prompt": "Explain quantum computing",
            "system_prompt": "You are a physics professor",
        }
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_with_custom_temperature(self, client: TestClient):
        """Test completion with custom temperature"""
        request = {"prompt": "Test prompt", "temperature": 0.3}
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_with_custom_max_tokens(self, client: TestClient):
        """Test completion with custom max_tokens"""
        request = {"prompt": "Test prompt", "max_tokens": 512}
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_with_metadata(self, client: TestClient):
        """Test completion with custom metadata"""
        request = {
            "prompt": "Test prompt",
            "metadata": {"user_id": "user123", "session": "session456"},
        }
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_invalid_temperature_low(self, client: TestClient):
        """Test completion with invalid temperature (too low)"""
        request = {"prompt": "Test prompt", "temperature": -0.5}
        response = client.post("/completion", json=request)
        assert response.status_code == 422  # Validation error

    def test_completion_invalid_temperature_high(self, client: TestClient):
        """Test completion with invalid temperature (too high)"""
        request = {"prompt": "Test prompt", "temperature": 3.0}
        response = client.post("/completion", json=request)
        assert response.status_code == 422  # Validation error

    def test_completion_invalid_max_tokens_low(self, client: TestClient):
        """Test completion with invalid max_tokens (too low)"""
        request = {"prompt": "Test prompt", "max_tokens": 0}
        response = client.post("/completion", json=request)
        assert response.status_code == 422  # Validation error

    def test_completion_invalid_max_tokens_high(self, client: TestClient):
        """Test completion with invalid max_tokens (too high)"""
        request = {"prompt": "Test prompt", "max_tokens": 10000}
        response = client.post("/completion", json=request)
        assert response.status_code == 422  # Validation error

    def test_completion_missing_prompt(self, client: TestClient):
        """Test completion without prompt (should fail validation)"""
        request = {"model": "gemini-pro"}
        response = client.post("/completion", json=request)
        assert response.status_code == 422

    def test_completion_empty_prompt(self, client: TestClient):
        """Test completion with empty prompt"""
        request = {"prompt": ""}
        response = client.post("/completion", json=request)
        # Should succeed (empty prompt is technically valid)
        assert response.status_code == 200

    def test_completion_long_prompt(self, client: TestClient):
        """Test completion with very long prompt"""
        long_prompt = "word " * 1000  # 1000 words
        request = {"prompt": long_prompt}
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_special_characters_prompt(self, client: TestClient):
        """Test completion with special characters in prompt"""
        request = {"prompt": "What is 2 + 2? Answer with symbols: !@#$%^&*()"}
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_unicode_prompt(self, client: TestClient):
        """Test completion with Unicode characters"""
        request = {"prompt": "Translate: Hello world to 中文 and Русский"}
        response = client.post("/completion", json=request)
        assert response.status_code == 200

    def test_completion_different_models(self, client: TestClient):
        """Test completion with different model names"""
        models = ["gemini-pro", "gemini-pro-vision", "custom-model"]
        for model in models:
            request = {"prompt": "test", "model": model}
            response = client.post("/completion", json=request)
            assert response.status_code == 200

    def test_completion_tokens_used_calculation(self, client: TestClient):
        """Test that tokens_used is calculated and positive"""
        request = {"prompt": "Short prompt"}
        response = client.post("/completion", json=request)
        data = response.json()
        assert data["tokens_used"] > 0

    def test_completion_correlation_id_present(self, client: TestClient):
        """Test that correlation_id is present in response"""
        request = {"prompt": "test"}
        response = client.post("/completion", json=request)
        data = response.json()
        assert len(data["correlation_id"]) > 0

    def test_completion_content_type(self, client: TestClient):
        """Test that response has correct content type"""
        request = {"prompt": "test"}
        response = client.post("/completion", json=request)
        assert response.headers["content-type"] == "application/json"

    def test_completion_invalid_json(self, client: TestClient):
        """Test completion with invalid JSON"""
        response = client.post(
            "/completion", data="not valid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_completion_concurrent_requests(self, client: TestClient):
        """Test multiple concurrent completion requests"""
        import concurrent.futures

        def make_request():
            return client.post("/completion", json={"prompt": "test"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(r.status_code == 200 for r in responses)


class TestCompletionWithAuth:
    """Test completion endpoint with authentication scenarios"""

    def test_completion_with_auth_headers(self, client: TestClient, auth_headers):
        """Test completion with authentication headers"""
        request = {"prompt": "test"}
        response = client.post("/completion", json=request, headers=auth_headers)
        assert response.status_code == 200

    def test_completion_without_auth_when_not_required(self, client: TestClient):
        """Test completion works without auth when REQUIRE_AUTH is false"""
        request = {"prompt": "test"}
        response = client.post("/completion", json=request)
        assert response.status_code == 200
