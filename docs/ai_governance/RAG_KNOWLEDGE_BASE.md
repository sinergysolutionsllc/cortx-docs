# RAG Knowledge Base Management

**Version:** 1.0.0
**Last Updated:** 2025-10-01
**Owner:** AI Platform Team
**Classification:** Internal

---

## Purpose

This document defines the management, maintenance, and governance of the CORTX Platform's Retrieval-Augmented Generation (RAG) knowledge base. The RAG system enhances AI capabilities by grounding responses in verified compliance documents, regulatory frameworks, and platform documentation.

---

## Overview

### What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that enhances Large Language Model (LLM) responses by:
1. Retrieving relevant context from a curated knowledge base
2. Injecting that context into the LLM prompt
3. Generating responses grounded in factual, domain-specific information

### Why RAG for CORTX?

**Benefits:**
- **Accuracy:** Reduce hallucinations by grounding responses in verified documents
- **Compliance:** Ensure AI recommendations align with regulatory frameworks
- **Context:** Provide domain expertise (Treasury rules, HIPAA controls, etc.)
- **Freshness:** Update knowledge without retraining models
- **Explainability:** Cite sources for AI-generated recommendations

**Use Cases:**
- Explain RulePack validation failures with regulatory context
- Generate WorkflowPacks based on compliance requirements
- Answer questions about platform capabilities and APIs
- Provide compliance guidance for Pack authors
- Suggest corrections for failed validations

---

## Architecture

### Vector Store

**Technology:** Sentence Transformers + PostgreSQL pgvector
**Embedding Model:** `all-MiniLM-L6-v2` (384 dimensions)
**Similarity Metric:** Cosine similarity
**Indexing:** HNSW (Hierarchical Navigable Small World)

**Configuration:**
```python
from sentence_transformers import SentenceTransformer

# Embedding model
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Vector store settings
VECTOR_DIMENSIONS = 384
SIMILARITY_THRESHOLD = 0.5
TOP_K_RESULTS = 5
MAX_CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50    # tokens
```

### Document Processing Pipeline

```
┌──────────────────┐
│ Source Documents │
│  (PDF, MD, TXT)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Text Extraction  │
│  (pypdf, pandoc) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    Chunking      │
│ (512 tokens max) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Embedding      │
│   Generation     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   PostgreSQL     │
│  Vector Storage  │
└──────────────────┘
```

### Retrieval Flow

```python
async def retrieve_context(query: str, top_k: int = 5) -> List[Document]:
    """Retrieve relevant context from knowledge base.

    Args:
        query: User query or prompt
        top_k: Number of results to return

    Returns:
        List of documents with content and metadata
    """
    # 1. Generate query embedding
    query_embedding = embedder.encode(query)

    # 2. Search vector store
    results = await vector_store.similarity_search(
        query_embedding,
        k=top_k,
        threshold=SIMILARITY_THRESHOLD
    )

    # 3. Apply keyword boosting
    for result in results:
        if any(keyword in result.content.lower()
               for keyword in query.lower().split()):
            result.score *= 1.2

    # 4. Re-rank by score
    results = sorted(results, key=lambda r: r.score, reverse=True)

    # 5. Return top results
    return results[:top_k]
```

---

## Knowledge Base Contents

### 1. Compliance & Regulatory Documents

#### Federal Financial Compliance
**Source:** US Department of Treasury, OMB

| Document | Version | Last Updated | Chunks | Status |
|----------|---------|--------------|--------|--------|
| OMB Circular A-136 | 2023 | 2023-06-15 | 342 | ✅ Active |
| GTAS Validation Rules | 2024 | 2024-01-01 | 204 | ✅ Active |
| Treasury Financial Manual | Vol 1, Part 2 | 2023-09-30 | 156 | ✅ Active |
| USSGL Account Attributes | FY 2024 | 2023-10-01 | 89 | ✅ Active |

**Coverage:** 791 chunks, ~405,000 tokens

#### HIPAA Compliance
**Source:** HHS Office for Civil Rights

| Document | Version | Last Updated | Chunks | Status |
|----------|---------|--------------|--------|--------|
| HIPAA Security Rule | Final Rule | 2003-02-20 | 128 | ✅ Active |
| HIPAA Privacy Rule | Final Rule | 2002-08-14 | 156 | ✅ Active |
| Breach Notification Rule | Final Rule | 2009-08-24 | 67 | ✅ Active |
| Technical Safeguards Guide | 2020 | 2020-05-15 | 94 | ✅ Active |

**Coverage:** 445 chunks, ~228,000 tokens

#### NIST Cybersecurity
**Source:** NIST Computer Security Resource Center

| Document | Version | Last Updated | Chunks | Status |
|----------|---------|--------------|--------|--------|
| NIST 800-53 Rev 5 | Revision 5 | 2020-09-23 | 1,247 | ✅ Active |
| FedRAMP Authorization Guide | v3.1 | 2021-06-08 | 234 | ✅ Active |
| NIST Cybersecurity Framework | v1.1 | 2018-04-16 | 187 | ✅ Active |

**Coverage:** 1,668 chunks, ~854,000 tokens

### 2. Platform Documentation

#### CORTX Platform APIs
**Source:** Internal OpenAPI specifications

| Service | Endpoints | Last Updated | Chunks | Status |
|---------|-----------|--------------|--------|--------|
| Gateway API | 12 | 2025-09-30 | 48 | ✅ Active |
| Identity API | 8 | 2025-09-30 | 32 | ✅ Active |
| AI Broker API | 15 | 2025-09-30 | 60 | ✅ Active |
| Validation API | 10 | 2025-09-30 | 40 | ✅ Active |
| Workflow API | 18 | 2025-09-30 | 72 | ✅ Active |
| Compliance API | 14 | 2025-09-30 | 56 | ✅ Active |

**Coverage:** 308 chunks, ~158,000 tokens

#### Pack Schemas & Examples
**Source:** cortx-packs repository

| Category | Packs | Last Updated | Chunks | Status |
|----------|-------|--------------|--------|--------|
| RulePack Schema | 1 | 2025-09-30 | 24 | ✅ Active |
| WorkflowPack Schema | 1 | 2025-09-30 | 32 | ✅ Active |
| Example RulePacks | 8 | 2025-09-30 | 96 | ✅ Active |
| Example WorkflowPacks | 5 | 2025-09-30 | 80 | ✅ Active |

**Coverage:** 232 chunks, ~119,000 tokens

### 3. Domain Knowledge

#### Federal Financial Management
**Source:** FedSuite documentation, Treasury guidance

| Topic | Documents | Chunks | Status |
|-------|-----------|--------|--------|
| Trial Balance Reconciliation | 3 | 67 | ✅ Active |
| GTAS Submission Process | 4 | 89 | ✅ Active |
| Treasury Account Symbols | 2 | 45 | ✅ Active |
| FBDI Integration | 2 | 38 | ✅ Active |

**Coverage:** 239 chunks, ~122,000 tokens

#### Healthcare Compliance
**Source:** MedSuite documentation, CMS guidance

| Topic | Documents | Chunks | Status |
|-------|-----------|--------|--------|
| Claims Verification | 2 | 56 | ✅ Active |
| HIPAA Audit Procedures | 3 | 78 | ✅ Active |
| EHR Integration | 1 | 34 | ✅ Active |

**Coverage:** 168 chunks, ~86,000 tokens

#### Real Estate & Property
**Source:** CorpSuite documentation, Maryland SDAT

| Topic | Documents | Chunks | Status |
|-------|-----------|--------|--------|
| Title Verification | 2 | 45 | ✅ Active |
| Property Search Procedures | 1 | 28 | ✅ Active |
| SDAT AUP Restrictions | 1 | 19 | ✅ Active |

**Coverage:** 92 chunks, ~47,000 tokens

---

## Total Knowledge Base Statistics

- **Total Documents:** 73
- **Total Chunks:** 3,943
- **Total Tokens:** ~2,019,000
- **Vector Dimensions:** 384
- **Storage Size:** ~1.5 GB (embeddings + metadata)
- **Last Full Update:** 2025-09-30

---

## Document Management

### Adding New Documents

**Process:**
1. **Source Verification:** Ensure document is authoritative and current
2. **License Check:** Verify we have rights to use (public domain, licensed, internal)
3. **Format Conversion:** Convert to plain text (Markdown preferred)
4. **Chunking:** Split into 512-token chunks with 50-token overlap
5. **Embedding Generation:** Generate vector embeddings
6. **Metadata Tagging:** Add source, date, version, category
7. **Quality Review:** Verify retrieval accuracy with test queries
8. **Indexing:** Insert into vector store with HNSW indexing

**Example Code:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime

async def add_document(
    content: str,
    source: str,
    category: str,
    version: str,
    metadata: dict
):
    """Add new document to knowledge base."""
    # 1. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        length_function=len
    )
    chunks = splitter.split_text(content)

    # 2. Generate embeddings
    embeddings = embedder.encode(chunks)

    # 3. Prepare metadata
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_metadata = {
            **metadata,
            "source": source,
            "category": category,
            "version": version,
            "chunk_id": i,
            "total_chunks": len(chunks),
            "added_at": datetime.utcnow().isoformat()
        }

        # 4. Insert into vector store
        await vector_store.insert(
            embedding=embedding,
            content=chunk,
            metadata=chunk_metadata
        )

    logger.info(
        "document.added",
        source=source,
        chunks=len(chunks),
        category=category
    )
```

### Updating Existing Documents

**When to Update:**
- New version of regulatory document published
- Platform API changes
- Schema modifications
- Corrections to existing content

**Process:**
1. **Mark Old Version:** Tag as deprecated (don't delete yet)
2. **Add New Version:** Follow "Adding New Documents" process
3. **Verify Retrieval:** Test queries to ensure new version retrieved
4. **Archive Old Version:** After 30 days, remove deprecated version
5. **Update Changelog:** Document changes in knowledge base log

**Example:**
```python
async def update_document(
    document_id: str,
    new_content: str,
    new_version: str
):
    """Update existing document with new version."""
    # 1. Deprecate old version
    await vector_store.update_metadata(
        document_id=document_id,
        metadata={"status": "deprecated", "deprecated_at": datetime.utcnow()}
    )

    # 2. Add new version
    await add_document(
        content=new_content,
        source=f"{document_id}",
        category=original_category,
        version=new_version,
        metadata={"replaces": document_id}
    )

    # 3. Schedule cleanup
    await schedule_cleanup(document_id, days=30)
```

### Removing Documents

**When to Remove:**
- Document superseded by newer version (after 30-day grace period)
- License expired or revoked
- Content no longer relevant
- Source deemed unreliable

**Process:**
1. **Verify No Dependencies:** Check if any packs reference this document
2. **Archive First:** Export to cold storage before deletion
3. **Soft Delete:** Mark as deleted, don't remove immediately
4. **Monitor Impact:** Track retrieval metrics for 7 days
5. **Hard Delete:** Permanently remove after verification period

---

## Retrieval Strategies

### Standard Retrieval
**Use Case:** General queries, broad topics
**Method:** Cosine similarity, top-k results
**Parameters:** k=5, threshold=0.5

```python
results = await retrieve_context(
    query="What are HIPAA technical safeguards?",
    top_k=5
)
```

### Keyword-Boosted Retrieval
**Use Case:** Specific terms, acronyms, regulatory references
**Method:** Cosine similarity + keyword matching bonus
**Parameters:** k=5, threshold=0.5, boost=1.2x

```python
async def retrieve_with_keyword_boost(query: str, keywords: List[str]):
    results = await retrieve_context(query, top_k=10)

    for result in results:
        if any(kw.lower() in result.content.lower() for kw in keywords):
            result.score *= 1.2

    return sorted(results, key=lambda r: r.score, reverse=True)[:5]
```

### Category-Filtered Retrieval
**Use Case:** Domain-specific queries
**Method:** Pre-filter by category before similarity search
**Parameters:** category filter, k=5

```python
results = await vector_store.similarity_search(
    query_embedding,
    k=5,
    filter={"category": "hipaa_compliance"}
)
```

### Multi-Query Retrieval
**Use Case:** Complex, multi-faceted questions
**Method:** Generate multiple query variations, merge results
**Parameters:** 3 query variations, k=3 per query, deduplicate

```python
async def multi_query_retrieval(original_query: str):
    # Generate query variations
    variations = await llm.generate([
        f"Rephrase this query: {original_query}",
        f"Break this into sub-questions: {original_query}"
    ])

    all_results = []
    for query in [original_query] + variations:
        results = await retrieve_context(query, top_k=3)
        all_results.extend(results)

    # Deduplicate and re-rank
    unique_results = deduplicate_by_content(all_results)
    return sorted(unique_results, key=lambda r: r.score, reverse=True)[:5]
```

---

## Quality Assurance

### Retrieval Accuracy Testing

**Test Set:** 100 curated query-answer pairs
**Success Criteria:** Correct answer in top-3 results for >90% of queries

**Example Test Cases:**
```python
TEST_CASES = [
    {
        "query": "What is the GTAS submission deadline?",
        "expected_source": "GTAS Validation Rules 2024",
        "expected_keywords": ["submission", "deadline", "calendar day"]
    },
    {
        "query": "How do I implement HIPAA access controls?",
        "expected_source": "HIPAA Security Rule",
        "expected_keywords": ["access control", "§164.312(a)(1)"]
    },
    {
        "query": "What are the RulePack severity levels?",
        "expected_source": "RulePack Schema",
        "expected_keywords": ["FATAL", "WARNING", "INFO"]
    }
]

async def test_retrieval_accuracy():
    correct = 0
    for test in TEST_CASES:
        results = await retrieve_context(test["query"], top_k=3)

        # Check if expected source in top 3
        if any(test["expected_source"] in r.metadata["source"] for r in results):
            correct += 1

    accuracy = correct / len(TEST_CASES)
    assert accuracy > 0.90, f"Retrieval accuracy {accuracy:.2%} below threshold"
```

### Embedding Drift Detection

**Monitor:** Cosine similarity distribution over time
**Alert:** If mean similarity drops >10% from baseline

```python
async def monitor_embedding_drift():
    # Sample random queries
    sample_queries = await get_random_queries(n=100)

    current_similarities = []
    for query in sample_queries:
        results = await retrieve_context(query, top_k=1)
        current_similarities.append(results[0].score)

    current_mean = np.mean(current_similarities)
    baseline_mean = await get_baseline_similarity()

    drift = (baseline_mean - current_mean) / baseline_mean

    if drift > 0.10:
        logger.warning(
            "embedding.drift.detected",
            current_mean=current_mean,
            baseline_mean=baseline_mean,
            drift_pct=drift * 100
        )
```

### Coverage Analysis

**Metric:** Percentage of queries with >0.5 similarity score
**Target:** >95% of queries return at least 1 result

```python
async def analyze_coverage(queries: List[str]):
    covered = 0
    for query in queries:
        results = await retrieve_context(query, top_k=1)
        if results and results[0].score > 0.5:
            covered += 1

    coverage = covered / len(queries)
    logger.info("rag.coverage", coverage_pct=coverage * 100)

    return coverage
```

---

## Performance Optimization

### Caching Strategy

**Cache Layer:** Redis
**TTL:** 1 hour for query results
**Cache Key:** SHA-256 hash of query + parameters

```python
import hashlib
import json

async def retrieve_with_cache(query: str, top_k: int = 5):
    # Generate cache key
    cache_key = hashlib.sha256(
        json.dumps({"query": query, "top_k": top_k}).encode()
    ).hexdigest()

    # Check cache
    cached = await redis.get(f"rag:{cache_key}")
    if cached:
        logger.info("rag.cache.hit", query=query)
        return json.loads(cached)

    # Retrieve from vector store
    results = await retrieve_context(query, top_k)

    # Cache results
    await redis.setex(
        f"rag:{cache_key}",
        3600,  # 1 hour TTL
        json.dumps([r.to_dict() for r in results])
    )

    logger.info("rag.cache.miss", query=query)
    return results
```

### Index Optimization

**Index Type:** HNSW (Hierarchical Navigable Small World)
**Parameters:**
- `m`: 16 (connections per layer)
- `ef_construction`: 200 (build-time accuracy)
- `ef_search`: 100 (query-time accuracy)

```sql
-- Create HNSW index
CREATE INDEX idx_embeddings_hnsw
ON knowledge_base
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);

-- Query with ef_search
SET hnsw.ef_search = 100;
SELECT * FROM knowledge_base
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

### Batch Retrieval

**Use Case:** Retrieve context for multiple queries at once
**Benefit:** Reduce database round-trips

```python
async def batch_retrieve(queries: List[str], top_k: int = 5):
    # Generate all embeddings at once
    query_embeddings = embedder.encode(queries)

    # Batch query vector store
    all_results = await vector_store.batch_similarity_search(
        embeddings=query_embeddings,
        k=top_k
    )

    return all_results
```

---

## Monitoring & Metrics

### Key Metrics

**Retrieval Metrics:**
- Query latency (p50, p95, p99)
- Cache hit rate
- Results per query (avg, median)
- Similarity scores (avg, distribution)

**Quality Metrics:**
- Retrieval accuracy (test set)
- Coverage rate (queries with results)
- User feedback (thumbs up/down on AI responses)

**System Metrics:**
- Vector store size (GB)
- Embedding generation time
- Index build time
- Storage growth rate

**Dashboards:**
```python
# Grafana dashboard queries
{
    "rag_query_latency_ms": "histogram(rag.query.duration)",
    "rag_cache_hit_rate": "sum(rag.cache.hit) / sum(rag.cache.total)",
    "rag_avg_similarity": "avg(rag.result.similarity)",
    "rag_results_per_query": "avg(rag.result.count)"
}
```

### Alerts

**Critical:**
- Retrieval accuracy <90% (test set)
- Query latency p99 >1000ms
- Vector store unavailable

**Warning:**
- Cache hit rate <50%
- Embedding drift >10%
- Coverage rate <95%

---

## Security & Privacy

### PII Redaction

**Before Embedding:**
All documents must be scanned for PII and redacted before embedding generation.

```python
def redact_pii_before_embedding(content: str) -> str:
    """Redact PII before generating embeddings."""
    # SSN
    content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', content)

    # Email
    content = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[REDACTED_EMAIL]',
        content
    )

    # Phone
    content = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[REDACTED_PHONE]', content)

    return content
```

### Access Control

**Knowledge Base Access:**
- Public documents: No restrictions
- Internal documents: Require authentication
- Tenant-specific documents: Tenant isolation

```python
async def retrieve_with_access_control(
    query: str,
    user_context: dict,
    top_k: int = 5
):
    results = await retrieve_context(query, top_k)

    # Filter based on user permissions
    filtered_results = [
        r for r in results
        if can_access_document(r.metadata, user_context)
    ]

    return filtered_results

def can_access_document(metadata: dict, user_context: dict) -> bool:
    """Check if user can access document."""
    doc_classification = metadata.get("classification", "public")

    if doc_classification == "public":
        return True

    if doc_classification == "internal":
        return user_context.get("authenticated", False)

    if doc_classification == "tenant_private":
        return metadata.get("tenant_id") == user_context.get("tenant_id")

    return False
```

---

## Maintenance Schedule

### Daily
- Monitor retrieval metrics
- Check cache hit rates
- Review error logs

### Weekly
- Run retrieval accuracy tests
- Analyze coverage metrics
- Review new document additions

### Monthly
- Embedding drift analysis
- Index optimization review
- Update deprecated documents
- Archive old versions

### Quarterly
- Full knowledge base audit
- Review and update test cases
- Re-evaluate document sources
- Update this document

---

## Changelog

**2025-10-01:**
- Initial knowledge base setup
- Added 73 documents (3,943 chunks)
- Configured HNSW indexing
- Implemented caching layer

---

## Contact

**RAG Knowledge Base Maintainers:**
- AI Platform Team: ai-platform@sinergysolutions.ai
- Slack: #rag-knowledge-base

**Request Document Addition:**
- Create GitHub issue with `rag-document` label
- Include source, category, and justification
- Tag AI platform team for review

---

**Document Control**
- **Version:** 1.0.0
- **Last Updated:** 2025-10-01
- **Review Cycle:** Quarterly
- **Next Review:** 2026-01-01
- **Approvers:** AI Platform Team
