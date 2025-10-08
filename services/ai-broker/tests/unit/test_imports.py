"""Test that all imports work correctly"""



class TestImports:
    """Test suite for verifying imports"""

    def test_fastapi_imports(self):
        """Verify FastAPI imports successfully"""
        from fastapi import Depends, FastAPI, HTTPException, Request
        from fastapi.responses import JSONResponse

        assert FastAPI is not None
        assert Request is not None
        assert Depends is not None
        assert HTTPException is not None
        assert JSONResponse is not None

    def test_pydantic_imports(self):
        """Verify Pydantic imports successfully"""
        from pydantic import BaseModel, Field

        assert BaseModel is not None
        assert Field is not None

    def test_httpx_import(self):
        """Verify httpx imports successfully"""
        import httpx

        assert httpx is not None

    def test_cortx_backend_imports(self):
        """Verify cortx_backend package imports successfully"""
        from cortx_backend.common.auth import (
            decode_token_optional,
            get_user_id_from_request,
            require_auth,
        )
        from cortx_backend.common.config import CORTXConfig
        from cortx_backend.common.http_client import CORTXClient
        from cortx_backend.common.logging import setup_logging
        from cortx_backend.common.metrics import instrument_metrics
        from cortx_backend.common.middleware import add_common_middleware
        from cortx_backend.common.tokens import EnvTokenProvider
        from cortx_backend.common.tracing import setup_tracing

        assert CORTXConfig is not None
        assert CORTXClient is not None
        assert callable(setup_logging)
        assert callable(instrument_metrics)
        assert callable(add_common_middleware)
        assert EnvTokenProvider is not None
        assert callable(setup_tracing)
        assert callable(get_user_id_from_request)
        assert callable(require_auth)
        assert callable(decode_token_optional)

    def test_app_main_imports(self):
        """Verify app.main module imports successfully"""
        from app.main import (
            CompletionRequest,
            CompletionResponse,
            EmbeddingRequest,
            EmbeddingResponse,
            app,
            mock_completion,
            mock_embedding,
        )

        assert app is not None
        assert CompletionRequest is not None
        assert CompletionResponse is not None
        assert EmbeddingRequest is not None
        assert EmbeddingResponse is not None
        assert callable(mock_completion)
        assert callable(mock_embedding)

    def test_google_cloud_optional_import(self):
        """Verify Google Cloud imports are optional"""
        # This should not raise an error even if not installed
        try:
            from google.cloud import aiplatform
            from google.oauth2 import service_account

            # If available, verify they're not None
            assert aiplatform is not None
            assert service_account is not None
        except ImportError:
            # This is expected if Google Cloud SDK not installed
            pass


class TestAppConfiguration:
    """Test app configuration and setup"""

    def test_app_title(self):
        """Test that app has correct title"""
        from app.main import app

        assert app.title == "PropVerify AI Broker Service"

    def test_app_version(self):
        """Test that app has version set"""
        from app.main import app

        assert app.version == "0.1.0"

    def test_vertex_available_constant(self):
        """Test VERTEX_AVAILABLE constant exists"""
        from app.main import VERTEX_AVAILABLE

        assert isinstance(VERTEX_AVAILABLE, bool)
