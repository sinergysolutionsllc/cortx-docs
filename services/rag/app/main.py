import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from app.chunking import chunk_text
from app.database import check_db_connection, get_db, init_db
from app.embeddings import generate_embedding, generate_embeddings_batch, preload_model
from app.models import Chunk, Document, QueryCache
from app.retrieval import RetrievalContext, RetrievedChunk, cascading_retrieval, hybrid_retrieval
from cortx_backend.common.auth import decode_token_optional, get_user_id_from_request, require_auth
from cortx_backend.common.config import CORTXConfig
from cortx_backend.common.http_client import CORTXClient
from cortx_backend.common.logging import setup_logging
from cortx_backend.common.metrics import instrument_metrics
from cortx_backend.common.middleware import add_common_middleware
from cortx_backend.common.tokens import EnvTokenProvider
from cortx_backend.common.tracing import setup_tracing
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = setup_logging("rag-svc")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("rag-svc startup: initializing database and models")

    # Check database connection
    if not check_db_connection():
        logger.error("Database connection failed. Service may not function correctly.")

    # Initialize database schema
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Preload embedding model
    try:
        preload_model()
    except Exception as e:
        logger.error(f"Failed to preload embedding model: {e}")

    logger.info("rag-svc startup complete")

    try:
        yield
    finally:
        try:
            client._client.close()  # type: ignore[attr-defined]
        except Exception:
            pass
        logger.info("rag-svc shutdown complete")


app = FastAPI(title="CORTX RAG Service", version="0.1.0", lifespan=lifespan)
setup_tracing("rag-svc", app)

# Initialize CORTX infrastructure
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


# ============================================================================
# Health and Meta Endpoints
# ============================================================================


@app.get("/healthz", tags=["health"])
async def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/readyz", tags=["health"])
async def readyz(db: Session = Depends(get_db)) -> JSONResponse:
    db_status = "connected" if check_db_connection() else "disconnected"

    # Count documents and chunks
    try:
        doc_count = db.query(Document).filter(Document.status == "active").count()
        chunk_count = db.query(Chunk).count()
    except Exception as e:
        logger.error(f"Failed to query database: {e}")
        doc_count = 0
        chunk_count = 0

    return JSONResponse(
        {
            "status": "ready",
            "database": db_status,
            "documents": doc_count,
            "chunks": chunk_count,
            "embedding_model": "all-MiniLM-L6-v2",
        }
    )


@app.get("/", tags=["meta"])
async def index(_claims: Optional[dict] = Depends(auth_dependency)) -> JSONResponse:
    return JSONResponse(
        {
            "name": "CORTX RAG Service",
            "version": app.version,
            "message": "Hierarchical RAG with cascading context retrieval",
            "features": [
                "4-level-hierarchy",
                "semantic-search",
                "hybrid-retrieval",
                "conversation-history",
                "semantic-caching",
            ],
        }
    )


# ============================================================================
# Request/Response Models
# ============================================================================


class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    level: str
    chunks_count: int
    status: str


class QueryRequest(BaseModel):
    query: str = Field(..., description="User's question")
    suite_id: Optional[str] = Field(None, description="Current suite context")
    module_id: Optional[str] = Field(None, description="Current module context")
    use_cache: bool = Field(True, description="Use semantic cache if available")
    use_hybrid: bool = Field(False, description="Use hybrid retrieval (vector + keyword)")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    max_tokens: int = Field(
        default=1000, ge=100, le=4000, description="Max tokens for LLM response"
    )


class QueryResponse(BaseModel):
    query: str
    answer: str
    chunks_used: int
    document_sources: List[str]
    model: str
    tokens_used: int
    cache_hit: bool
    correlation_id: str


class RetrieveRequest(BaseModel):
    query: str
    suite_id: Optional[str] = None
    module_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)
    use_hybrid: bool = False


class RetrieveResponse(BaseModel):
    query: str
    chunks: List[Dict[str, Any]]
    retrieval_time_ms: float


# ============================================================================
# Document Management Endpoints
# ============================================================================


@app.post("/documents/upload", tags=["documents"], response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    level: str = Form(...),
    suite_id: Optional[str] = Form(None),
    module_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    access_level: str = Form("internal"),
    _claims: Optional[dict] = Depends(auth_dependency),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Upload and process a document for RAG.

    Steps:
    1. Read file content
    2. Chunk text into semantic segments
    3. Generate embeddings for each chunk
    4. Store document and chunks in database
    """
    user_id = get_user_id_from_request(request)
    tenant_id = _claims.get("tenant_id", "default") if _claims else "default"

    logger.info(f"Document upload: title='{title}', level={level}, user={user_id}")

    try:
        # Read file content
        content = await file.read()
        text_content = content.decode("utf-8")

        # Chunk text
        chunks = chunk_text(text_content, chunk_size=512, chunk_overlap=50)

        if not chunks:
            raise HTTPException(status_code=400, detail="Document contains no usable content")

        # Generate embeddings in batch
        chunk_texts = [c.content for c in chunks]
        embeddings = generate_embeddings_batch(chunk_texts)

        # Create document record
        doc = Document(
            tenant_id=tenant_id,
            level=level,
            suite_id=suite_id,
            module_id=module_id,
            title=title,
            description=description,
            source_type=file.content_type or "text/plain",
            file_size=len(content),
            access_level=access_level,
            doc_metadata={
                "original_filename": file.filename,
                "uploaded_by": user_id,
                "upload_timestamp": datetime.utcnow().isoformat(),
            },
        )
        db.add(doc)
        db.flush()

        # Create chunk records
        for chunk_meta, embedding in zip(chunks, embeddings):
            chunk_rec = Chunk(
                document_id=doc.id,
                ord=chunk_meta.ord,
                content=chunk_meta.content,
                content_hash=Chunk.compute_hash(chunk_meta.content),
                heading=chunk_meta.heading,
                token_count=chunk_meta.token_count,
                embedding=embedding,
            )
            db.add(chunk_rec)

        db.commit()

        logger.info(f"Document uploaded successfully: id={doc.id}, chunks={len(chunks)}")

        return JSONResponse(
            DocumentUploadResponse(
                id=str(doc.id),
                title=doc.title,
                level=doc.level,
                chunks_count=len(chunks),
                status="active",
            ).dict()
        )

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents", tags=["documents"])
async def list_documents(
    level: Optional[str] = None,
    suite_id: Optional[str] = None,
    module_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _claims: Optional[dict] = Depends(auth_dependency),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """List documents with optional filtering."""
    tenant_id = _claims.get("tenant_id", "default") if _claims else "default"

    query = db.query(Document).filter(Document.tenant_id == tenant_id, Document.status == "active")

    if level:
        query = query.filter(Document.level == level)
    if suite_id:
        query = query.filter(Document.suite_id == suite_id)
    if module_id:
        query = query.filter(Document.module_id == module_id)

    total = query.count()
    docs = query.order_by(Document.created_at.desc()).limit(limit).offset(offset).all()

    return JSONResponse(
        {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "level": doc.level,
                    "suite_id": doc.suite_id,
                    "module_id": doc.module_id,
                    "source_type": doc.source_type,
                    "created_at": doc.created_at.isoformat(),
                    "chunk_count": len(doc.chunks),
                }
                for doc in docs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@app.delete("/documents/{document_id}", tags=["documents"])
async def delete_document(
    document_id: str,
    _claims: Optional[dict] = Depends(auth_dependency),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Soft-delete a document."""
    tenant_id = _claims.get("tenant_id", "default") if _claims else "default"

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id)
        .first()
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "deleted"
    db.commit()

    return JSONResponse({"status": "deleted", "id": document_id})


# ============================================================================
# RAG Query Endpoints
# ============================================================================


@app.post("/query", tags=["rag"], response_model=QueryResponse)
async def rag_query(
    request: Request,
    query_req: QueryRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Main RAG query endpoint.

    Combines retrieval and generation:
    1. Check semantic cache
    2. Retrieve relevant chunks (cascading or hybrid)
    3. Build prompt with context
    4. Call AI Broker for generation
    5. Return answer with citations
    """
    corr_id = request.state.correlation_id
    user_id = get_user_id_from_request(request)
    tenant_id = _claims.get("tenant_id", "default") if _claims else "default"

    logger.info(
        f"RAG query: '{query_req.query[:50]}...' suite={query_req.suite_id}, module={query_req.module_id}"
    )

    start_time = time.time()

    # Check semantic cache
    cache_hit = False
    if query_req.use_cache:
        cached = check_cache(
            query_req.query, tenant_id, query_req.suite_id, query_req.module_id, db
        )
        if cached:
            logger.info("Cache hit!")
            cache_hit = True
            return JSONResponse(
                QueryResponse(
                    query=query_req.query,
                    answer=cached["answer"],
                    chunks_used=cached["chunks_used"],
                    document_sources=cached["document_sources"],
                    model=cached["model"],
                    tokens_used=0,
                    cache_hit=True,
                    correlation_id=corr_id,
                ).dict()
            )

    # Retrieve relevant chunks
    context = RetrievalContext(
        tenant_id=tenant_id,
        user_id=user_id,
        suite_id=query_req.suite_id,
        module_id=query_req.module_id,
    )

    if query_req.use_hybrid:
        chunks = hybrid_retrieval(query_req.query, context, db, top_k=query_req.top_k)
    else:
        chunks = cascading_retrieval(query_req.query, context, db, top_k=query_req.top_k)

    if not chunks:
        # No relevant context found
        answer = "I don't have enough information in my knowledge base to answer that question. Could you rephrase or provide more context?"
        return JSONResponse(
            QueryResponse(
                query=query_req.query,
                answer=answer,
                chunks_used=0,
                document_sources=[],
                model="none",
                tokens_used=0,
                cache_hit=False,
                correlation_id=corr_id,
            ).dict()
        )

    # Build prompt with retrieved context
    context_text = "\n\n".join(
        [
            f"[Source: {c.document_title} - {c.heading or 'Main Content'}]\n{c.content}"
            for c in chunks
        ]
    )

    system_prompt = build_system_prompt(query_req.suite_id, query_req.module_id)

    user_prompt = f"""Based on the following context, answer the user's question. Always cite your sources.

CONTEXT:
{context_text}

USER QUESTION:
{query_req.query}

Please provide a comprehensive answer that:
1. Addresses the question directly
2. Cites specific sources from the context
3. Highlights any compliance or policy considerations
4. Uses clear, professional language
"""

    # Call AI Broker for generation
    ai_broker_url = os.getenv("CORTX_AI_BROKER_URL", "http://ai-broker:8085")

    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"{ai_broker_url}/completion",
                json={
                    "prompt": user_prompt,
                    "system_prompt": system_prompt,
                    "model": "gemini-1.5-flash",
                    "temperature": 0.3,
                    "max_tokens": query_req.max_tokens,
                },
            )
            response.raise_for_status()
            completion = response.json()

        answer = completion.get("text", "No response generated")
        model = completion.get("model", "unknown")
        tokens_used = completion.get("tokens_used", 0)

    except Exception as e:
        logger.error(f"AI Broker call failed: {e}")
        answer = "I encountered an error generating a response. Please try again."
        model = "error"
        tokens_used = 0

    # Store in cache
    if query_req.use_cache and not cache_hit:
        store_in_cache(
            query_req.query,
            answer,
            chunks,
            model,
            tenant_id,
            query_req.suite_id,
            query_req.module_id,
            db,
        )

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(
        f"Query completed in {elapsed_ms:.0f}ms, {len(chunks)} chunks, {tokens_used} tokens"
    )

    return JSONResponse(
        QueryResponse(
            query=query_req.query,
            answer=answer,
            chunks_used=len(chunks),
            document_sources=list(set(c.document_title for c in chunks)),
            model=model,
            tokens_used=tokens_used,
            cache_hit=False,
            correlation_id=corr_id,
        ).dict()
    )


@app.post("/retrieve", tags=["rag"], response_model=RetrieveResponse)
async def retrieve_chunks(
    request: Request,
    retrieve_req: RetrieveRequest,
    _claims: Optional[dict] = Depends(auth_dependency),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Retrieve relevant chunks without LLM generation.

    Useful for debugging or building custom prompts.
    """
    user_id = get_user_id_from_request(request)
    tenant_id = _claims.get("tenant_id", "default") if _claims else "default"

    start_time = time.time()

    context = RetrievalContext(
        tenant_id=tenant_id,
        user_id=user_id,
        suite_id=retrieve_req.suite_id,
        module_id=retrieve_req.module_id,
    )

    if retrieve_req.use_hybrid:
        chunks = hybrid_retrieval(retrieve_req.query, context, db, top_k=retrieve_req.top_k)
    else:
        chunks = cascading_retrieval(retrieve_req.query, context, db, top_k=retrieve_req.top_k)

    elapsed_ms = (time.time() - start_time) * 1000

    return JSONResponse(
        RetrieveResponse(
            query=retrieve_req.query,
            chunks=[
                {
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "document_title": c.document_title,
                    "document_level": c.document_level,
                    "heading": c.heading,
                    "content": c.content,
                    "similarity": c.similarity,
                    "context_boost": c.context_boost,
                    "final_score": c.final_score,
                }
                for c in chunks
            ],
            retrieval_time_ms=elapsed_ms,
        ).dict()
    )


# ============================================================================
# Helper Functions
# ============================================================================


def build_system_prompt(suite_id: Optional[str], module_id: Optional[str]) -> str:
    """Build context-aware system prompt."""
    base = "You are ThinkTank, an AI assistant for the CORTX Platform. You provide policy-first guidance with emphasis on compliance and security."

    if suite_id == "fedsuite":
        return (
            base
            + " Focus on federal compliance (NIST 800-53, FedRAMP, OMB circulars) and use federal agency examples."
        )
    elif suite_id == "corpsuite":
        return (
            base + " Focus on corporate compliance (SOC 2, ISO 27001) and private sector examples."
        )
    elif suite_id == "medsuite":
        return base + " Focus on healthcare compliance (HIPAA, 21 CFR Part 11) and protect PHI."
    else:
        return base


def check_cache(
    query: str, tenant_id: str, suite_id: Optional[str], module_id: Optional[str], db: Session
) -> Optional[Dict]:
    """Check semantic cache for similar query."""
    try:
        query_embedding = generate_embedding(query)
        query_hash = QueryCache.compute_query_hash(query)

        # Check exact match first
        exact = (
            db.query(QueryCache)
            .filter(
                QueryCache.query_hash == query_hash,
                QueryCache.tenant_id == tenant_id,
                QueryCache.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if exact:
            exact.hit_count += 1
            exact.last_accessed_at = datetime.utcnow()
            db.commit()
            return {
                "answer": exact.response_text,
                "chunks_used": len(exact.chunk_ids or []),
                "document_sources": [],
                "model": exact.model,
            }

        # TODO: Check semantic similarity for near-matches

        return None

    except Exception as e:
        logger.error(f"Cache check failed: {e}")
        return None


def store_in_cache(
    query: str,
    answer: str,
    chunks: List[RetrievedChunk],
    model: str,
    tenant_id: str,
    suite_id: Optional[str],
    module_id: Optional[str],
    db: Session,
) -> None:
    """Store query/answer in semantic cache."""
    try:
        query_embedding = generate_embedding(query)
        query_hash = QueryCache.compute_query_hash(query)

        cache_entry = QueryCache(
            query_text=query,
            query_hash=query_hash,
            query_embedding=query_embedding,
            suite_id=suite_id,
            module_id=module_id,
            tenant_id=tenant_id,
            response_text=answer,
            document_ids=[c.document_id for c in chunks],
            chunk_ids=[c.chunk_id for c in chunks],
            model=model,
            hit_count=0,
            expires_at=datetime.utcnow() + timedelta(hours=1),  # 1-hour TTL
        )

        db.add(cache_entry)
        db.commit()

    except Exception as e:
        logger.error(f"Failed to store in cache: {e}")
        db.rollback()
