"""Integration tests for /models endpoint"""

from fastapi.testclient import TestClient


class TestModelsEndpoint:
    """Test suite for /models endpoint"""

    def test_models_endpoint_success(self, client: TestClient):
        """Test /models endpoint returns 200 OK"""
        response = client.get("/models")
        assert response.status_code == 200

    def test_models_response_format(self, client: TestClient):
        """Test /models endpoint response format"""
        response = client.get("/models")
        data = response.json()

        # Check all required fields are present
        assert "models" in data
        assert "vertex_available" in data
        assert "project_configured" in data

        # Validate field types
        assert isinstance(data["models"], dict)
        assert isinstance(data["vertex_available"], bool)
        assert isinstance(data["project_configured"], bool)

    def test_models_structure(self, client: TestClient):
        """Test models response has correct structure"""
        response = client.get("/models")
        data = response.json()

        models = data["models"]

        # Should have both text_generation and embeddings categories
        assert "text_generation" in models
        assert "embeddings" in models

        # Both should be lists
        assert isinstance(models["text_generation"], list)
        assert isinstance(models["embeddings"], list)

    def test_text_generation_models(self, client: TestClient):
        """Test text generation models are properly formatted"""
        response = client.get("/models")
        data = response.json()

        text_gen_models = data["models"]["text_generation"]

        # Should have at least some models
        assert len(text_gen_models) > 0

        # Check structure of each model
        for model in text_gen_models:
            assert "id" in model
            assert "name" in model
            assert "provider" in model
            assert "capabilities" in model

            assert isinstance(model["id"], str)
            assert isinstance(model["name"], str)
            assert isinstance(model["provider"], str)
            assert isinstance(model["capabilities"], list)

    def test_embedding_models(self, client: TestClient):
        """Test embedding models are properly formatted"""
        response = client.get("/models")
        data = response.json()

        embedding_models = data["models"]["embeddings"]

        # Should have at least some models
        assert len(embedding_models) > 0

        # Check structure of each model
        for model in embedding_models:
            assert "id" in model
            assert "name" in model
            assert "provider" in model
            assert "dimensions" in model

            assert isinstance(model["id"], str)
            assert isinstance(model["name"], str)
            assert isinstance(model["provider"], str)
            assert isinstance(model["dimensions"], int)

    def test_gemini_pro_model_present(self, client: TestClient):
        """Test that Gemini Pro model is in the list"""
        response = client.get("/models")
        data = response.json()

        text_gen_models = data["models"]["text_generation"]
        model_ids = [m["id"] for m in text_gen_models]

        assert "gemini-pro" in model_ids

    def test_gemini_pro_vision_model_present(self, client: TestClient):
        """Test that Gemini Pro Vision model is in the list"""
        response = client.get("/models")
        data = response.json()

        text_gen_models = data["models"]["text_generation"]
        model_ids = [m["id"] for m in text_gen_models]

        assert "gemini-pro-vision" in model_ids

    def test_textembedding_gecko_model_present(self, client: TestClient):
        """Test that Text Embedding Gecko model is in the list"""
        response = client.get("/models")
        data = response.json()

        embedding_models = data["models"]["embeddings"]
        model_ids = [m["id"] for m in embedding_models]

        assert "textembedding-gecko" in model_ids

    def test_gemini_pro_capabilities(self, client: TestClient):
        """Test Gemini Pro model capabilities"""
        response = client.get("/models")
        data = response.json()

        text_gen_models = data["models"]["text_generation"]
        gemini_pro = next(m for m in text_gen_models if m["id"] == "gemini-pro")

        assert "text-generation" in gemini_pro["capabilities"]
        assert "function-calling" in gemini_pro["capabilities"]
        assert gemini_pro["provider"] == "google"

    def test_gemini_pro_vision_capabilities(self, client: TestClient):
        """Test Gemini Pro Vision model capabilities"""
        response = client.get("/models")
        data = response.json()

        text_gen_models = data["models"]["text_generation"]
        gemini_vision = next(m for m in text_gen_models if m["id"] == "gemini-pro-vision")

        assert "text-generation" in gemini_vision["capabilities"]
        assert "vision" in gemini_vision["capabilities"]
        assert "multimodal" in gemini_vision["capabilities"]
        assert gemini_vision["provider"] == "google"

    def test_embedding_model_dimensions(self, client: TestClient):
        """Test that embedding models report correct dimensions"""
        response = client.get("/models")
        data = response.json()

        embedding_models = data["models"]["embeddings"]

        for model in embedding_models:
            # Gecko models should have 768 dimensions
            if "gecko" in model["id"]:
                assert model["dimensions"] == 768

    def test_models_vertex_status(self, client: TestClient):
        """Test vertex_available status reflects environment"""
        response = client.get("/models")
        data = response.json()

        # In test environment, we expect Vertex to be available (library)
        # but project not configured
        assert isinstance(data["vertex_available"], bool)

    def test_models_project_configured_status(self, client: TestClient):
        """Test project_configured reflects environment"""
        response = client.get("/models")
        data = response.json()

        # In test environment, VERTEX_PROJECT_ID should not be set
        assert data["project_configured"] is False

    def test_models_content_type(self, client: TestClient):
        """Test /models endpoint returns JSON content type"""
        response = client.get("/models")
        assert response.headers["content-type"] == "application/json"

    def test_models_no_auth_required(self, client: TestClient):
        """Test that /models endpoint doesn't require authentication when disabled"""
        # Should work without any auth headers
        response = client.get("/models")
        assert response.status_code == 200

    def test_models_with_auth_headers(self, client: TestClient, auth_headers):
        """Test /models endpoint works with auth headers"""
        response = client.get("/models", headers=auth_headers)
        assert response.status_code == 200

    def test_models_idempotent(self, client: TestClient):
        """Test that /models is idempotent (multiple calls same result)"""
        responses = [client.get("/models") for _ in range(3)]
        assert all(r.status_code == 200 for r in responses)

        # All responses should be identical
        first_data = responses[0].json()
        assert all(r.json() == first_data for r in responses)

    def test_models_all_providers_google(self, client: TestClient):
        """Test that all models currently use Google as provider"""
        response = client.get("/models")
        data = response.json()

        all_models = data["models"]["text_generation"] + data["models"]["embeddings"]

        # Currently all models should be from Google
        assert all(m["provider"] == "google" for m in all_models)

    def test_models_response_caching(self, client: TestClient):
        """Test that models response is consistent across requests"""
        response1 = client.get("/models")
        response2 = client.get("/models")

        # Responses should be identical
        assert response1.json() == response2.json()


class TestModelsEndpointEdgeCases:
    """Test edge cases for /models endpoint"""

    def test_models_accepts_query_parameters(self, client: TestClient):
        """Test that /models endpoint ignores unknown query parameters"""
        response = client.get("/models?unknown_param=value")
        assert response.status_code == 200

    def test_models_post_method_not_allowed(self, client: TestClient):
        """Test that POST method is not allowed on /models"""
        response = client.post("/models", json={})
        assert response.status_code == 405  # Method not allowed

    def test_models_put_method_not_allowed(self, client: TestClient):
        """Test that PUT method is not allowed on /models"""
        response = client.put("/models", json={})
        assert response.status_code == 405  # Method not allowed

    def test_models_delete_method_not_allowed(self, client: TestClient):
        """Test that DELETE method is not allowed on /models"""
        response = client.delete("/models")
        assert response.status_code == 405  # Method not allowed
