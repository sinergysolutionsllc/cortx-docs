import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Google Cloud imports (optional - will gracefully degrade if not available)
try:
    from google.cloud import aiplatform
    from google.oauth2 import service_account

    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    print("⚠️  Google Cloud AI Platform not available. Running in mock mode.")

from cortx_backend.common.auth import decode_token_optional, get_user_id_from_request, require_auth
from cortx_backend.common.config import CORTXConfig
from cortx_backend.common.http_client import CORTXClient
from cortx_backend.common.logging import setup_logging
from cortx_backend.common.metrics import instrument_metrics
from cortx_backend.common.middleware import add_common_middleware
from cortx_backend.common.tokens import EnvTokenProvider
from cortx_backend.common.tracing import setup_tracing

logger = setup_logging("ai-broker-svc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ai-broker-svc startup complete")

    # Initialize Vertex AI if available
    if VERTEX_AVAILABLE:
        project_id = os.getenv("VERTEX_PROJECT_ID")
        location = os.getenv("VERTEX_LOCATION", "us-central1")
        if project_id:
            try:
                aiplatform.init(project=project_id, location=location)
                logger.info(f"✅ Vertex AI initialized: project={project_id}, location={location}")
            except Exception as e:
                logger.warning(f"Could not initialize Vertex AI: {e}")
        else:
            logger.warning("VERTEX_PROJECT_ID not set. AI features will use mock responses.")

    try:
        yield
    finally:
        try:
            client._client.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        logger.info("ai-broker-svc shutdown complete")


app = FastAPI(title="PropVerify AI Broker Service", version="0.1.0", lifespan=lifespan)
setup_tracing("ai-broker-svc", app)

# Initialize CORTX infrastructure singletons
cfg = CORTXConfig.from_env()
client = CORTXClient(cfg, EnvTokenProvider())

# Apply common middleware and metrics
add_common_middleware(app)
instrument_metrics(app)


def auth_dependency(request: Request) -> Optional[dict]:
    if os.getenv("REQUIRE_AUTH", "false").lower() in {"1", "true", "yes"}:
        return require_auth(request)
    else:
        return decode_token_optional(request)


@app.get("/healthz", tags=["health"])
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/readyz", tags=["health"])
async def readyz() -> JSONResponse:
    vertex_status = "available" if VERTEX_AVAILABLE else "unavailable"
    project_id = os.getenv("VERTEX_PROJECT_ID")
    return JSONResponse(
        {"status": "ready", "vertex_ai": vertex_status, "project_configured": bool(project_id)}
    )


@app.get("/", tags=["meta"])
async def index(_claims: Optional[dict] = Depends(auth_dependency)) -> JSONResponse:
    return JSONResponse(
        {
            "name": "PropVerify AI Broker Service",
            "version": app.version,
            "message": "AI/ML inference gateway for Vertex AI and other models",
            "features": ["text-generation", "embeddings", "function-calling", "streaming"],
        }
    )


class CompletionRequest(BaseModel):
    """Request model for text completion."""

    prompt: str = Field(..., description="Text prompt for completion")
    model: str = Field(default="gemini-pro", description="Model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1024, ge=1, le=8192, description="Maximum tokens to generate")
    stream: bool = Field(default=False, description="Whether to stream responses")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class CompletionResponse(BaseModel):
    """Response model for text completion."""

    text: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used")
    tokens_used: int = Field(..., description="Total tokens used")
    finish_reason: str = Field(..., description="Reason for completion finish")
    correlation_id: str = Field(..., description="Correlation ID for tracing")


class EmbeddingRequest(BaseModel):
    """Request model for text embeddings."""

    text: str = Field(..., description="Text to embed")
    model: str = Field(default="textembedding-gecko", description="Embedding model")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""

    embedding: List[float] = Field(..., description="Vector embedding")
    model: str = Field(..., description="Model used")
    dimensions: int = Field(..., description="Embedding dimensions")
    correlation_id: str = Field(..., description="Correlation ID for tracing")


def mock_completion(prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
    """Generate a mock completion response for development/testing."""
    mock_responses = [
        "This is a mock AI response. Configure VERTEX_PROJECT_ID to use real AI.",
        f"Mock AI received your prompt: '{prompt[:50]}...'",
        "AI Broker is running in mock mode. Real AI features require Google Cloud credentials.",
    ]

    import random

    response_text = random.choice(mock_responses)

    return {
        "text": response_text,
        "tokens_used": len(prompt.split()) + len(response_text.split()),
        "finish_reason": "mock_complete",
    }


def mock_embedding(text: str) -> List[float]:
    """Generate a mock embedding for development/testing."""
    # Simple hash-based mock embedding (768 dimensions like BERT)
    import hashlib

    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()

    # Generate 768-dimensional embedding from hash
    embedding = []
    for i in range(768):
        byte_val = hash_bytes[i % len(hash_bytes)]
        # Normalize to [-1, 1] range
        normalized = (byte_val / 127.5) - 1.0
        embedding.append(normalized)

    return embedding


@app.post("/completion", tags=["ai"], response_model=CompletionResponse)
async def generate_completion(
    request: Request,
    completion_req: CompletionRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Generate text completion using AI model.

    Supports streaming and non-streaming modes.
    Uses Vertex AI if configured, otherwise returns mock responses.
    """
    corr_id = request.state.correlation_id
    user_id = get_user_id_from_request(request)

    logger.info(
        f"Completion request: model={completion_req.model}, tokens={completion_req.max_tokens}"
    )

    try:
        if VERTEX_AVAILABLE and os.getenv("VERTEX_PROJECT_ID"):
            # Real Vertex AI implementation
            try:
                from vertexai.preview.generative_models import GenerativeModel

                model = GenerativeModel(completion_req.model)

                # Build prompt with system message if provided
                full_prompt = completion_req.prompt
                if completion_req.system_prompt:
                    full_prompt = f"{completion_req.system_prompt}\n\n{completion_req.prompt}"

                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": completion_req.temperature,
                        "max_output_tokens": completion_req.max_tokens,
                    },
                )

                result = CompletionResponse(
                    text=response.text,
                    model=completion_req.model,
                    tokens_used=len(full_prompt.split())
                    + len(response.text.split()),  # Approximate
                    finish_reason="stop",
                    correlation_id=corr_id,
                )

            except Exception as e:
                logger.error(f"Vertex AI error: {e}. Falling back to mock.")
                mock_result = mock_completion(
                    completion_req.prompt, completion_req.temperature, completion_req.max_tokens
                )
                result = CompletionResponse(
                    text=mock_result["text"],
                    model=f"{completion_req.model} (mock)",
                    tokens_used=mock_result["tokens_used"],
                    finish_reason=mock_result["finish_reason"],
                    correlation_id=corr_id,
                )
        else:
            # Mock mode
            mock_result = mock_completion(
                completion_req.prompt, completion_req.temperature, completion_req.max_tokens
            )
            result = CompletionResponse(
                text=mock_result["text"],
                model=f"{completion_req.model} (mock)",
                tokens_used=mock_result["tokens_used"],
                finish_reason=mock_result["finish_reason"],
                correlation_id=corr_id,
            )

        logger.info(f"Completion generated: {result.tokens_used} tokens")
        return JSONResponse(result.dict())

    except Exception as e:
        logger.error(f"Completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")


@app.post("/embedding", tags=["ai"], response_model=EmbeddingResponse)
async def generate_embedding(
    request: Request,
    embedding_req: EmbeddingRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """Generate vector embedding for text.

    Uses Vertex AI Text Embeddings if configured, otherwise returns mock embeddings.
    """
    corr_id = request.state.correlation_id
    user_id = get_user_id_from_request(request)

    logger.info(
        f"Embedding request: model={embedding_req.model}, text_len={len(embedding_req.text)}"
    )

    try:
        if VERTEX_AVAILABLE and os.getenv("VERTEX_PROJECT_ID"):
            # Real Vertex AI implementation
            try:
                from vertexai.language_models import TextEmbeddingModel

                model = TextEmbeddingModel.from_pretrained(embedding_req.model)
                embeddings = model.get_embeddings([embedding_req.text])

                if embeddings and len(embeddings) > 0:
                    embedding_vector = embeddings[0].values

                    result = EmbeddingResponse(
                        embedding=embedding_vector,
                        model=embedding_req.model,
                        dimensions=len(embedding_vector),
                        correlation_id=corr_id,
                    )
                else:
                    raise ValueError("No embeddings returned from Vertex AI")

            except Exception as e:
                logger.error(f"Vertex AI embedding error: {e}. Falling back to mock.")
                mock_embedding_vector = mock_embedding(embedding_req.text)
                result = EmbeddingResponse(
                    embedding=mock_embedding_vector,
                    model=f"{embedding_req.model} (mock)",
                    dimensions=len(mock_embedding_vector),
                    correlation_id=corr_id,
                )
        else:
            # Mock mode
            mock_embedding_vector = mock_embedding(embedding_req.text)
            result = EmbeddingResponse(
                embedding=mock_embedding_vector,
                model=f"{embedding_req.model} (mock)",
                dimensions=len(mock_embedding_vector),
                correlation_id=corr_id,
            )

        logger.info(f"Embedding generated: {result.dimensions} dimensions")
        return JSONResponse(result.dict())

    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")


@app.get("/models", tags=["ai"])
async def list_models(
    _claims: Optional[dict] = Depends(auth_dependency),
) -> JSONResponse:
    """List available AI models."""

    models = {
        "text_generation": [
            {
                "id": "gemini-pro",
                "name": "Gemini Pro",
                "provider": "google",
                "capabilities": ["text-generation", "function-calling"],
            },
            {
                "id": "gemini-pro-vision",
                "name": "Gemini Pro Vision",
                "provider": "google",
                "capabilities": ["text-generation", "vision", "multimodal"],
            },
        ],
        "embeddings": [
            {
                "id": "textembedding-gecko",
                "name": "Text Embedding Gecko",
                "provider": "google",
                "dimensions": 768,
            },
            {
                "id": "textembedding-gecko-multilingual",
                "name": "Text Embedding Gecko Multilingual",
                "provider": "google",
                "dimensions": 768,
            },
        ],
    }

    return JSONResponse(
        {
            "models": models,
            "vertex_available": VERTEX_AVAILABLE,
            "project_configured": bool(os.getenv("VERTEX_PROJECT_ID")),
        }
    )
