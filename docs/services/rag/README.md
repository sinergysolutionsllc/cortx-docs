# RAG Service with ThinkTank (Port 8138)

**Status:** ✅ Implemented | **Version:** 0.1.0

## Overview

The RAG (Retrieval-Augmented Generation) service provides hierarchical, context-aware knowledge retrieval for the CORTX platform. It powers **ThinkTank**, an AI assistant interface that delivers intelligent, contextually relevant help across all platform modules, dashboards, and workflows.

## Core Capabilities

### Hierarchical Knowledge Architecture

4-level contextual hierarchy:

- **Platform** - Global platform knowledge (no scope)
- **Suite** - Suite-specific knowledge (e.g., FedSuite, CorpSuite)
- **Module** - Module-specific knowledge (e.g., Dataflow, Reconciliation)
- **Entity** - Tenant/entity-specific knowledge (user/org data)

### Retrieval Augmented Generation

- **Semantic Search**: Vector similarity using pgvector embeddings
- **Hybrid Retrieval**: Combined vector + keyword search
- **Cascading Context**: Queries cascade from specific to general
- **Semantic Caching**: Cache answers for similar questions
- **Conversation History**: Multi-turn contextual conversations

### Document Management

- **Upload & Index**: Process documents with automatic chunking
- **Batch Embedding**: Efficient vector generation
- **Multi-Tenant**: Tenant-scoped document isolation
- **Soft Delete**: Non-destructive document removal

## Architecture Diagram

```mermaid
flowchart TB
    Client[UI Components] -->|Query| RAG[RAG Service :8138]

    subgraph "Frontend Layer"
        FAB[ThinkTank FAB]
        FullPage[ThinkTank Full Page]
        ContextHook[useThinkTankContext]
    end

    subgraph "RAG Service Core"
        QueryAPI[Query API]
        DocAPI[Document API]
        RetrievalEngine[Retrieval Engine]
        ChunkingEngine[Chunking Engine]
        EmbeddingGen[Embedding Generator]
    end

    subgraph "Retrieval Strategies"
        Cascading[Cascading Retrieval]
        Hybrid[Hybrid Search]
        SemanticCache[Semantic Cache]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        PGVector[(pgvector Extension)]
        Documents[Documents Table]
        Chunks[Chunks Table]
        Cache[Query Cache Table]
    end

    FAB --> QueryAPI
    FullPage --> QueryAPI
    ContextHook --> QueryAPI

    QueryAPI --> RetrievalEngine
    DocAPI --> ChunkingEngine
    ChunkingEngine --> EmbeddingGen

    RetrievalEngine --> Cascading
    RetrievalEngine --> Hybrid
    RetrievalEngine --> SemanticCache

    Cascading --> PGVector
    Hybrid --> PGVector
    SemanticCache --> Cache

    EmbeddingGen --> Chunks
    Chunks --> Documents
    Documents --> DB
    Chunks --> DB
    Cache --> DB

    RetrievalEngine -->|LLM Generation| AIBroker[AI Broker :8085]
    DocAPI -->|Audit Events| Ledger[Ledger Service :8136]
```

## Key Features

### Semantic Search with pgvector

Vector embeddings powered by Sentence Transformers:

- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Embedding Speed**: ~100 chunks/second
- **Cosine Similarity**: L2-normalized vectors
- **Index Type**: HNSW for fast retrieval

### Intelligent Text Chunking

Semantic-aware chunking strategy:

- **Chunk Size**: 512 tokens (configurable)
- **Overlap**: 50 tokens to preserve context
- **Heading Detection**: Preserve document structure
- **Token Counting**: Accurate tokenization for LLMs

### Cascading Context Retrieval

Query execution cascades through hierarchy:

1. Search entity-specific knowledge
2. Fallback to module-level knowledge
3. Fallback to suite-level knowledge
4. Finally search platform-global knowledge

Returns most specific relevant context first.

### Hybrid Retrieval

Combines vector and keyword search:

- **Vector Search**: Semantic similarity (80% weight)
- **Keyword Search**: BM25 full-text search (20% weight)
- **Fusion**: RRF (Reciprocal Rank Fusion)
- **Use Case**: Technical queries with specific terminology

### Semantic Query Caching

Intelligent answer caching:

- **Similarity Threshold**: Cache hit if query embedding within 0.95 cosine similarity
- **TTL**: 24-hour cache expiration
- **Hit Rate**: ~30-40% for common questions
- **Cache Invalidation**: Automatic on document updates

### Conversation Context

Multi-turn conversation support:

- Conversation history stored per session
- Context passed to LLM for coherent responses
- Previous Q&A pairs inform current query
- Session management via conversation IDs

## API Endpoints

### Health & Status

- `GET /healthz` - Kubernetes liveness probe
- `GET /readyz` - Readiness probe with database status
- `GET /` - Service metadata and features

### Query Endpoints

- `POST /query` - Query with LLM-generated answer

  ```json
  {
    "query": "How do I configure dataflow mappings?",
    "suite_id": "fedsuite",
    "module_id": "dataflow",
    "top_k": 5,
    "use_cache": true,
    "use_hybrid": false,
    "max_tokens": 1000
  }
  ```

- `POST /retrieve` - Retrieve chunks without LLM generation

  ```json
  {
    "query": "dataflow configuration",
    "suite_id": "fedsuite",
    "module_id": "dataflow",
    "top_k": 5,
    "use_hybrid": true
  }
  ```

### Document Management

- `POST /documents/upload` - Upload and index document (multipart form)
  - **Fields**: `file`, `title`, `level`, `suite_id`, `module_id`, `description`, `access_level`
  - **Returns**: Document ID, chunk count, status

- `GET /documents` - List indexed documents
  - **Filters**: `level`, `suite_id`, `module_id`, `limit`, `offset`
  - **Returns**: Paginated document list

- `DELETE /documents/{document_id}` - Soft-delete document
  - Marks document as deleted (preserves for audit)

### Conversation Management

- `POST /conversations` - Create new conversation session
- `GET /conversations/{conversation_id}` - Get conversation history
- `DELETE /conversations/{conversation_id}` - End conversation

## Database Schema

### Documents Table (`rag_documents`)

```sql
CREATE TABLE rag_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    level VARCHAR(50) NOT NULL,  -- platform, suite, module, entity
    suite_id VARCHAR(100),
    module_id VARCHAR(100),
    title TEXT NOT NULL,
    description TEXT,
    source_type VARCHAR(100),  -- text/plain, application/pdf, etc.
    file_size INTEGER,
    access_level VARCHAR(50) DEFAULT 'internal',
    status VARCHAR(50) DEFAULT 'active',  -- active, deleted
    doc_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_docs_tenant ON rag_documents(tenant_id);
CREATE INDEX idx_docs_level ON rag_documents(level);
CREATE INDEX idx_docs_suite ON rag_documents(suite_id);
CREATE INDEX idx_docs_module ON rag_documents(module_id);
CREATE INDEX idx_docs_status ON rag_documents(status);
```

### Chunks Table (`rag_chunks`)

```sql
CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES rag_documents(id) ON DELETE CASCADE,
    ord INTEGER NOT NULL,  -- Chunk order in document
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    heading TEXT,
    token_count INTEGER,
    embedding vector(384),  -- pgvector type
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON rag_chunks(document_id);
CREATE INDEX idx_chunks_embedding ON rag_chunks USING ivfflat (embedding vector_cosine_ops);
```

### Query Cache Table (`rag_query_cache`)

```sql
CREATE TABLE rag_query_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    query_embedding vector(384),
    answer TEXT NOT NULL,
    chunks_used INTEGER,
    model VARCHAR(100),
    tokens_used INTEGER,
    context_scope JSONB,  -- {suite_id, module_id, entity_id}
    hit_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE INDEX idx_cache_query_hash ON rag_query_cache(query_hash);
CREATE INDEX idx_cache_embedding ON rag_query_cache USING ivfflat (query_embedding vector_cosine_ops);
CREATE INDEX idx_cache_expires ON rag_query_cache(expires_at);
```

### Conversations Table (`rag_conversations`)

```sql
CREATE TABLE rag_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    context JSONB,  -- {suite_id, module_id, entity_id}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Messages Table (`rag_messages`)

```sql
CREATE TABLE rag_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES rag_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- user, assistant
    content TEXT NOT NULL,
    chunks_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Configuration

### Environment Variables

```bash
# Database (required)
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx

# AI Broker (for LLM generation)
CORTX_AI_BROKER_URL=http://localhost:8085

# Gateway (for proxied requests)
CORTX_GATEWAY_URL=http://localhost:8080

# Authentication (optional)
REQUIRE_AUTH=false  # Set to "true" for production

# Service Port
PORT=8138

# Logging
LOG_LEVEL=INFO

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Sentence Transformers model

# Retrieval Settings
DEFAULT_TOP_K=5
MAX_TOP_K=20
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Cache Settings
CACHE_SIMILARITY_THRESHOLD=0.95
CACHE_TTL_HOURS=24
```

### Database Setup

```bash
# Create database
createdb cortx

# Enable pgvector extension
psql cortx -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations (automatic on startup)
# The service will create tables on first run
```

## Usage Examples

### Upload Document

```bash
curl -X POST http://localhost:8138/documents/upload \
  -H "X-Tenant-ID: tenant-123" \
  -F "file=@dataflow-guide.md" \
  -F "title=Dataflow Configuration Guide" \
  -F "level=module" \
  -F "suite_id=fedsuite" \
  -F "module_id=dataflow" \
  -F "description=Complete guide to dataflow setup"
```

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Dataflow Configuration Guide",
  "level": "module",
  "chunks_count": 42,
  "status": "active"
}
```

### Query with LLM Answer

```bash
curl -X POST http://localhost:8138/query \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I configure dataflow mappings?",
    "suite_id": "fedsuite",
    "module_id": "dataflow",
    "top_k": 5,
    "use_cache": true
  }'
```

Response:

```json
{
  "query": "How do I configure dataflow mappings?",
  "answer": "To configure dataflow mappings, navigate to the Dataflow module...",
  "chunks_used": 5,
  "document_sources": ["Dataflow Configuration Guide", "API Reference"],
  "model": "claude-3-5-sonnet-20241022",
  "tokens_used": 487,
  "cache_hit": false,
  "correlation_id": "req_abc123"
}
```

### Retrieve Chunks Only (No LLM)

```bash
curl -X POST http://localhost:8138/retrieve \
  -H "X-Tenant-ID: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "dataflow API endpoints",
    "suite_id": "fedsuite",
    "module_id": "dataflow",
    "top_k": 3,
    "use_hybrid": true
  }'
```

Response:

```json
{
  "query": "dataflow API endpoints",
  "chunks": [
    {
      "content": "The Dataflow API provides these endpoints...",
      "document_title": "API Reference",
      "score": 0.87,
      "heading": "Dataflow Endpoints"
    }
  ],
  "retrieval_time_ms": 23.4
}
```

### List Documents

```bash
curl "http://localhost:8138/documents?suite_id=fedsuite&module_id=dataflow&limit=10" \
  -H "X-Tenant-ID: tenant-123"
```

### Delete Document

```bash
curl -X DELETE http://localhost:8138/documents/{document_id} \
  -H "X-Tenant-ID: tenant-123"
```

### Health Check

```bash
curl http://localhost:8138/readyz
```

Response:

```json
{
  "status": "ready",
  "database": "connected",
  "documents": 142,
  "chunks": 2847,
  "embedding_model": "all-MiniLM-L6-v2"
}
```

## Integration Patterns

### ThinkTank Frontend Integration

React/Next.js component integration:

```tsx
import { ThinkTankAssistant } from '@/components/thinktank'
import { createRAGService } from '@/services/rag'
import { useThinkTankContext } from '@/hooks/useThinkTankContext'

export default function DashboardPage() {
  // Automatically detects context from URL
  const context = useThinkTankContext()  // {suite_id, module_id}

  // Create RAG client
  const ragService = createRAGService({
    baseUrl: process.env.NEXT_PUBLIC_RAG_URL || 'http://localhost:8138'
  })

  return (
    <main>
      {/* Your page content */}

      {/* ThinkTank floating assistant */}
      <ThinkTankAssistant
        ragService={ragService}
        context={context}
      />
    </main>
  )
}
```

### Backend Service Integration

Python service calling RAG API:

```python
import httpx

async def get_ai_assistance(query: str, suite_id: str = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8138/query",
            headers={"X-Tenant-ID": "tenant-123"},
            json={
                "query": query,
                "suite_id": suite_id,
                "top_k": 5
            }
        )
        return response.json()
```

### Context-Aware Queries

The service automatically cascades through context levels:

```python
# Entity-specific query (most specific)
query(query="...", suite_id="fedsuite", module_id="dataflow", entity_id="acme-corp")

# Module-level query
query(query="...", suite_id="fedsuite", module_id="dataflow")

# Suite-level query
query(query="...", suite_id="fedsuite")

# Platform-global query (most general)
query(query="...")
```

## Performance

### Throughput

- **Document Indexing**: ~10 documents/second (depends on size)
- **Chunk Embedding**: ~100 chunks/second
- **Query Latency**: 50-200ms (retrieval only)
- **LLM Response**: 2-5s (with AI Broker generation)
- **Cache Hit**: <10ms response time

### Scalability

- **Horizontal Scaling**: Multiple RAG service instances
- **Database Connection Pool**: 20 connections, 40 overflow
- **Async Processing**: Non-blocking I/O for all operations
- **Index Performance**: HNSW index for sub-linear search

### Resource Requirements

- **Memory**: ~2GB per instance (model + connection pool)
- **CPU**: 2 cores recommended
- **Disk**: Depends on document corpus size
- **GPU**: Not required (CPU inference is fast enough)

## Security

### Multi-Tenancy

- Tenant-scoped document access
- Row-level security via `tenant_id`
- Tenant context from JWT claims
- Cross-tenant data isolation

### Access Control

- Optional JWT authentication (`REQUIRE_AUTH=true`)
- Document-level access control (`access_level` field)
- Internal/external/public visibility levels
- Future: Role-based document permissions

### Data Protection

- Soft delete preserves audit trail
- Content hashing prevents duplicate storage
- Encrypted database connections (TLS)
- PII/PHI redaction support (future)

## Monitoring & Logging

### Structured Logging

JSON logs with:

- Request correlation IDs
- Tenant context
- Query performance metrics
- Document indexing events
- Cache hit/miss rates

### Health Checks

- **Liveness**: `/healthz` - Service running?
- **Readiness**: `/readyz` - Database connected? Model loaded?
- **Metrics**: Document count, chunk count, model status

### Metrics (Future)

Recommended Prometheus metrics:

- `rag_queries_total{cache_hit=true|false}` - Query count
- `rag_query_duration_seconds` - Query latency
- `rag_documents_indexed_total` - Documents processed
- `rag_chunks_created_total` - Chunks generated
- `rag_cache_hit_rate` - Cache effectiveness
- `rag_embedding_duration_seconds` - Embedding generation time

## Development

### Local Setup

```bash
# Navigate to RAG service directory
cd /Users/michael/Development/sinergysolutionsllc/services/rag

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ensure PostgreSQL is running with pgvector
psql cortx -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run service
PYTHONPATH=../../packages/cortx_backend:. \
PORT=8138 \
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx \
CORTX_AI_BROKER_URL=http://localhost:8085 \
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8138 --reload
```

### Testing

```bash
# Test health
curl http://localhost:8138/healthz

# Test readiness
curl http://localhost:8138/readyz

# Upload test document
curl -X POST http://localhost:8138/documents/upload \
  -F "file=@test-doc.md" \
  -F "title=Test Document" \
  -F "level=platform"

# Query test
curl -X POST http://localhost:8138/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 3}'
```

### Docker

```bash
# Build container
docker build -f services/rag/Dockerfile -t cortx-rag:0.1.0 .

# Run container
docker run -p 8138:8138 \
  -e POSTGRES_URL=postgresql://cortx:password@db:5432/cortx \
  -e CORTX_AI_BROKER_URL=http://ai-broker:8085 \
  cortx-rag:0.1.0
```

## Troubleshooting

### Database Connection Errors

```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
psql "postgresql://cortx:cortx_dev_password@localhost:5432/cortx" -c "SELECT 1;"

# Verify pgvector extension
psql cortx -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Embedding Model Issues

```bash
# Model downloads on first run to ~/.cache/torch/sentence_transformers/
ls ~/.cache/torch/sentence_transformers/

# Force re-download
rm -rf ~/.cache/torch/sentence_transformers/sentence-transformers_all-MiniLM-L6-v2
```

### No Query Results

```bash
# Check if documents are indexed
curl http://localhost:8138/documents

# Verify chunks exist
psql cortx -c "SELECT COUNT(*) FROM rag_chunks;"

# Check vector index
psql cortx -c "SELECT COUNT(*) FROM rag_chunks WHERE embedding IS NOT NULL;"
```

## Roadmap

### Phase 1: Enhanced Retrieval

- Reranking with cross-encoder model
- Query expansion via LLM
- Multi-query retrieval strategies
- Parent-child document chunking

### Phase 2: Advanced Features

- PDF/Word document parsing
- Image/diagram extraction and indexing
- Code snippet search and execution
- Structured data (tables, JSON) retrieval

### Phase 3: Personalization

- User preference learning
- Personalized ranking
- Feedback-based model fine-tuning
- Collaborative filtering

### Phase 4: Enterprise Features

- SSO integration for access control
- Compliance tracking (audit who accessed what)
- Multi-language support
- On-premise deployment options

## Documentation

- **OpenAPI Spec**: [openapi.yaml](./openapi.yaml)
- **Source Code**: `/services/rag/app/`
- **Hierarchical RAG Architecture**: `/docs/architecture/HIERARCHICAL_RAG_ARCHITECTURE.md`
- **ThinkTank Vision**: `/docs/architecture/THINKTANK_VISION.md`

## Support

For issues or questions:

- GitHub Issues: [sinergysolutionsllc/sinergysolutionsllc](https://github.com/sinergysolutionsllc/sinergysolutionsllc/issues)
- Internal Documentation: `/docs/services/rag/`
- Platform Team: Platform Services Team
