# CORTX RAG Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

Provides intelligent document retrieval and AI-powered question answering through a hierarchical RAG system that organizes knowledge across platform, suite, module, and entity levels.

### 1.2 Scope

- Document ingestion and chunking
- Vector embedding generation
- Hierarchical knowledge organization
- Similarity search and retrieval
- Context-aware answer generation
- Knowledge base management
- Metadata filtering

### 1.3 Out of Scope

- Document OCR (handled by OCR service)
- Model training (handled by AI Broker)
- Real-time document updates (batch processing)

## 2. Key Features

### 2.1 Hierarchical Knowledge Base

- **Level 1 - Platform**: Universal CORTX policies and best practices
- **Level 2 - Suite**: Domain-specific regulations (Fed, Corp, Med, Gov)
- **Level 3 - Module**: Technical schemas and validation logic
- **Level 4 - Entity**: Tenant/org-specific rules and SOPs

### 2.2 Document Processing

- **Chunking**: Split documents into semantic chunks
- **Embedding**: Generate vector embeddings via AI Broker
- **Metadata**: Extract and store document metadata
- **Versioning**: Track document versions

### 2.3 Retrieval

- **Vector Search**: Cosine similarity search
- **Hybrid Search**: Combine vector + keyword search
- **Filtered Search**: Filter by level, suite, module, entity
- **Ranked Results**: Return top-k most relevant chunks

### 2.4 Generation

- **Contextual Answers**: Generate answers from retrieved context
- **Source Citations**: Include source documents in response
- **Confidence Scoring**: Rate answer confidence
- **Streaming**: Stream long-form answers

## 3. API Contracts

### 3.1 Ingest Document

```
POST /v1/ingest
Body:
  {
    "content": "Document text...",
    "metadata": {
      "level": "suite",
      "suite": "fedsuite",
      "module": "reconciliation",
      "source": "CFR 1234.56",
      "version": "1.0"
    }
  }
Response: 201 Created
  {
    "document_id": "uuid",
    "chunks_created": 15,
    "embeddings_generated": 15
  }
```

### 3.2 Query

```
POST /v1/query
Body:
  {
    "question": "What are the reconciliation requirements?",
    "filters": {
      "level": "suite",
      "suite": "fedsuite"
    },
    "top_k": 5
  }
Response: 200 OK
  {
    "answer": "Generated answer...",
    "confidence": 0.92,
    "sources": [
      {
        "chunk_id": "uuid",
        "content": "...",
        "metadata": {...},
        "similarity": 0.87
      }
    ]
  }
```

### 3.3 Search

```
POST /v1/search
Body:
  {
    "query": "reconciliation",
    "filters": {
      "suite": "fedsuite"
    },
    "top_k": 10
  }
Response: 200 OK
  {
    "results": [
      {
        "chunk_id": "uuid",
        "content": "...",
        "metadata": {...},
        "similarity": 0.85
      }
    ]
  }
```

## 4. Dependencies

### 4.1 Upstream

- **PostgreSQL with pgvector**: Vector storage and search
- **AI Broker**: Embedding generation and answer generation
- **OCR Service**: Document text extraction (optional)

### 4.2 Downstream

- **Validation Service**: AI-powered validation
- **Gateway**: Explanation generation
- **ThinkTank**: Conversational AI

## 5. Data Models

### 5.1 Document

```python
@dataclass
class Document:
    document_id: UUID
    level: Literal["platform", "suite", "module", "entity"]
    suite: Optional[str]
    module: Optional[str]
    entity_id: Optional[str]
    content: str
    metadata: dict
    version: str
    created_at: datetime
```

### 5.2 Chunk

```python
@dataclass
class Chunk:
    chunk_id: UUID
    document_id: UUID
    content: str
    embedding: List[float]  # 768 dimensions
    chunk_index: int
    metadata: dict
```

### 5.3 Query Result

```python
@dataclass
class QueryResult:
    answer: str
    confidence: float
    sources: List[Source]
    processing_time_ms: int
```

## 6. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Required | PostgreSQL with pgvector |
| `AI_BROKER_URL` | <http://localhost:8085> | AI Broker service |
| `CHUNK_SIZE` | 512 | Tokens per chunk |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `EMBEDDING_MODEL` | textembedding-gecko@003 | Embedding model |
| `GENERATION_MODEL` | text-bison@002 | Generation model |

## 7. Chunking Strategy

### 7.1 Semantic Chunking

- Split on paragraph boundaries
- Maintain sentence integrity
- Target chunk size: 512 tokens
- Overlap: 50 tokens for context

### 7.2 Metadata Preservation

- Level, suite, module, entity
- Source document reference
- Section/subsection headers
- Version and timestamp

## 8. Search Algorithms

### 8.1 Vector Search

- Cosine similarity on embeddings
- GPU-accelerated if available
- Top-k results

### 8.2 Hybrid Search

- Combine vector similarity + BM25 keyword search
- Weighted fusion of scores
- Better recall for specific terms

### 8.3 Filtered Search

- Pre-filter by metadata before similarity
- Reduces search space
- Faster for large knowledge bases

## 9. Performance Characteristics

### 9.1 Latency

- Document ingestion: < 5s per document
- Query (with generation): < 2s
- Search only: < 500ms
- Embedding generation: < 300ms per chunk

### 9.2 Throughput

- 100 queries/second
- 10 document ingestions/second

### 9.3 Resource Requirements

- CPU: 2 cores baseline, 8 cores under load
- Memory: 2GB baseline, 8GB under load
- PostgreSQL: 500GB storage, 1000 IOPS

## 10. Monitoring

### 10.1 Metrics

- Query latency (p50, p95, p99)
- Document ingestion rate
- Embedding cache hit rate
- Answer confidence distribution
- Search result relevance

### 10.2 Alerts

- Query latency > 5s
- Low confidence answers > 30%
- Database connection issues
- Embedding service failures

## 11. Future Enhancements

- Multi-modal RAG (images, tables)
- Fine-tuned embeddings per domain
- Active learning from user feedback
- Automatic knowledge base updates
- Cross-lingual search

## 12. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |
