# CORTX Hierarchical RAG Architecture
**Date:** 2025-10-01
**Status:** Strategic Design
**Team:** Tech Architect Analysis

---

## Executive Summary

This document defines a **4-level hierarchical RAG (Retrieval-Augmented Generation) architecture** for the CORTX Platform, enabling contextual AI assistance that understands knowledge at Platform, Suite, Module, and Entity levels.

### Key Design Principles
1. **Contextual Awareness**: AI can access knowledge from all relevant levels
2. **Hierarchical Retrieval**: Search starts narrow (Module) and expands outward (Suite → Platform)
3. **Scoped Permissions**: Entity-level knowledge is tenant-isolated
4. **Unified Management**: Single RAG Management UI for ingesting and organizing knowledge
5. **Platform Integration**: Centralized **svc-rag (8138)** with ingestion from **svc-ocr (8137)** and provenance via **svc-ledger (8136)**
 
--- 

## 1. Hierarchical Knowledge Architecture

### 1.2 Platform Integration (svc-rag, svc-ocr, svc-ledger)

- **svc-rag (8138):** Central RAG APIs for ingest → chunk → embed → retrieve across four scopes (Platform, Suite, Module, Entity). Exposes Admin UI hooks used by Designer.
- **svc-ocr (8137):** Document → text/fields extraction; normalized `DocumentExtraction` JSON is ingested by svc-rag with appropriate scope metadata.
- **svc-ledger (8136):** Append-only, SHA-256 hash-chained evidence for all compliance-relevant RAG actions (ingest, delete, query served to end users), enabling end-to-end provenance.

### 1.1 Four-Level Knowledge Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEVEL 1: PLATFORM                            │
│  Universal knowledge applicable to ALL suites & modules         │
│  ├── NIST 800-53, FedRAMP, HIPAA, SOC 2 controls               │
│  ├── CORTX Platform documentation                               │
│  ├── General AI/ML best practices                               │
│  ├── Security & compliance frameworks                           │
│  └── Cross-industry standards                                   │
│  Scope: Global | Permissions: Public                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LEVEL 2: SUITE                               │
│  Domain-specific knowledge for a vertical                       │
│                                                                 │
│  FedSuite:                                                      │
│  ├── OMB Circulars (A-11, A-123, A-136)                        │
│  ├── Treasury GTAS Reporting Guide                             │
│  ├── Federal accounting standards (USSGL, FASAB)               │
│  └── Agency-wide policies (DOD FMR, VA directives)             │
│                                                                 │
│  CorpSuite:                                                     │
│  ├── Real estate law (Maryland, Virginia)                      │
│  ├── Procurement regulations (FAR, state rules)                │
│  └── Corporate compliance (SOX, GAAP)                          │
│                                                                 │
│  MedSuite:                                                      │
│  ├── HIPAA Privacy & Security Rules                            │
│  ├── CMS guidelines                                             │
│  └── Healthcare billing standards (ICD-10, CPT)                │
│                                                                 │
│  Scope: Suite-wide | Permissions: Suite users                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LEVEL 3: MODULE                              │
│  Module-specific technical knowledge                            │
│                                                                 │
│  FedTransform:                                                  │
│  ├── Oracle EBS table schemas (GL, AP, AR, FA)                 │
│  ├── PeopleSoft FSCM structure                                 │
│  ├── SAP ECC/S4 HANA data models                               │
│  ├── Workday Financial mappings                                │
│  └── FBDI template specifications                              │
│                                                                 │
│  PropVerify:                                                    │
│  ├── Maryland SDAT API documentation                           │
│  ├── MDLandRec data dictionary                                 │
│  ├── Title examination checklists                              │
│  └── Lien/encumbrance lookup procedures                        │
│                                                                 │
│  FedReconcile:                                                  │
│  ├── GTAS submission schemas (ATB, BETC)                       │
│  ├── Trial Balance validation rules (204+ rules)               │
│  └── Reconciliation workflows                                  │
│                                                                 │
│  Scope: Module-wide | Permissions: Module users                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LEVEL 4: ENTITY (Tenant)                     │
│  Organization/tenant-specific knowledge                         │
│                                                                 │
│  Examples:                                                      │
│  ├── Agency-specific accounting policies                        │
│  ├── Department-specific approval workflows                     │
│  ├── Custom chart of accounts mappings                         │
│  ├── Organization-specific compliance interpretations          │
│  └── Internal standard operating procedures (SOPs)             │
│                                                                 │
│  Scope: Tenant-specific | Permissions: Tenant users only       │
│  Security: RLS enforced, encrypted at rest                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Contextual Retrieval Strategy

### 2.1 Cascading Context Pattern

**Scenario:** User working in FedTransform asks: *"How do I map Oracle GL balances to GTAS?"*

**Retrieval flow:**
```
1. MODULE (FedTransform):
   ├── Search: Oracle EBS GL tables, FBDI mappings
   └── Retrieve: Top 5 chunks (score > 0.7)

2. SUITE (FedSuite):
   ├── Search: GTAS reporting requirements, USSGL mapping rules
   └── Retrieve: Top 5 chunks (score > 0.7)

3. ENTITY (Tenant: DOD Finance):
   ├── Search: DOD-specific GL to GTAS mappings, agency policies
   └── Retrieve: Top 3 chunks (score > 0.8)

4. PLATFORM (if needed):
   ├── Search: Data transformation best practices
   └── Retrieve: Top 2 chunks (score > 0.75)

5. COMBINE CONTEXT:
   ├── Module: 5 chunks (most specific)
   ├── Suite: 5 chunks (domain rules)
   ├── Entity: 3 chunks (org-specific)
   ├── Platform: 2 chunks (general guidance)
   └── Total: 15 chunks passed to LLM
```

### 2.2 Context Priority Scoring

```python
def calculate_context_score(chunk, level, base_similarity_score):
    """
    Boost scores based on hierarchical relevance
    """
    level_boost = {
        "entity": 0.15,    # Most specific to user's org
        "module": 0.10,    # Most specific to current task
        "suite": 0.05,     # Domain-relevant
        "platform": 0.0    # Baseline
    }

    return base_similarity_score + level_boost[level]
```

### 2.3 Smart Context Expansion

**When to expand to higher levels:**
1. **Insufficient results** at lower level (< 3 chunks above threshold)
2. **Explicit cross-domain query** (e.g., "What are the compliance requirements?")
3. **User requests broader context** (e.g., "Include federal regulations")

**When to restrict context:**
1. **Highly technical query** (e.g., "What's the Oracle GL_BALANCES table structure?")
2. **Entity-specific query** (e.g., "What's our approval workflow?")
3. **Performance optimization** (fewer tokens = faster, cheaper)

---

## 3. Vector Store Architecture

### 3.1 Database Schema Design

**PostgreSQL with pgvector extension:**

```sql
-- Unified RAG schema using pgvector with level-based scoping
CREATE SCHEMA IF NOT EXISTS rag;

CREATE TABLE rag.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,                -- 'global' for Platform
    level TEXT NOT NULL CHECK (level IN ('platform','suite','module','entity')),
    suite_id TEXT,                          -- nullable when not applicable
    module_id TEXT,                         -- nullable when not applicable
    title TEXT,
    source_type TEXT,                       -- upload|url|api
    source_uri TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    ingested_at TIMESTAMPTZ DEFAULT now(),
    ingested_by TEXT,
    version TEXT,
    tags TEXT[]
);

CREATE TABLE rag.chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES rag.documents(id) ON DELETE CASCADE,
    ord INT NOT NULL,
    content TEXT NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb,        -- page, section, headers
    embedding VECTOR(384)                  -- using 384-dim embeddings
);

-- Row-Level Security for tenant isolation on documents (applies to chunks via FK)
ALTER TABLE rag.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY rag_docs_tenant_isolation ON rag.documents
  USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Similarity indexes
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON rag.chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Helpful metadata indexes
CREATE INDEX IF NOT EXISTS idx_docs_level ON rag.documents(level);
CREATE INDEX IF NOT EXISTS idx_docs_suite_module ON rag.documents(suite_id, module_id);
CREATE INDEX IF NOT EXISTS idx_docs_tenant ON rag.documents(tenant_id);
```

### 3.2 Vector Search Implementation

```python
# services/rag/app/hierarchical_retrieval.py
from typing import List, Dict, Any, Optional
import asyncpg

class HierarchicalRAGRetriever:
    """
    Retrieve context from unified rag.documents/rag.chunks across levels.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def retrieve_context(
        self,
        query_embedding: List[float],
        tenant_id: str,
        suite_id: str,
        module_id: str,
        levels: List[str] = ["entity", "module", "suite", "platform"],
        k_per_level: Optional[Dict[str, int]] = None,
        boosts: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        if k_per_level is None:
            k_per_level = {"entity": 3, "module": 5, "suite": 5, "platform": 2}
        if boosts is None:
            boosts = {"entity": 0.15, "module": 0.10, "suite": 0.05, "platform": 0.0}

        results: List[Dict[str, Any]] = []
        for level in levels:
            rows = await self._search_level(
                level, query_embedding, tenant_id, suite_id, module_id, k_per_level[level]
            )
            for r in rows:
                r["adjusted_score"] = float(r["similarity_score"]) + boosts.get(level, 0.0)
                r["level"] = level
            results.extend(rows)

        # Sort by adjusted score and return
        results.sort(key=lambda x: x["adjusted_score"], reverse=True)
        return results

    async def _search_level(
        self,
        level: str,
        embedding: List[float],
        tenant_id: str,
        suite_id: str,
        module_id: str,
        k: int
    ) -> List[Dict[str, Any]]:
        filters = []
        params = [embedding]

        if level == "entity":
            filters.append("d.tenant_id = $2")
            params.append(tenant_id)
            if suite_id:
                filters.append("d.suite_id = $3")
                params.append(suite_id)
            if module_id:
                filters.append("(d.module_id = $4 OR d.module_id IS NULL)")
                params.append(module_id)
        elif level == "module":
            filters.append("d.level = 'module'")
            filters.append("d.suite_id = $2")
            filters.append("d.module_id = $3")
            params.extend([suite_id, module_id])
        elif level == "suite":
            filters.append("d.level = 'suite'")
            filters.append("d.suite_id = $2")
            params.append(suite_id)
        else:  # platform
            filters.append("d.level = 'platform'")
            # no extra params

        # Build dynamic WHERE with defaults
        where_clause = " AND ".join(filters) if filters else "TRUE"

        query = f"""
            SELECT
                c.id as chunk_id,
                d.id as document_id,
                d.title,
                d.level,
                d.suite_id,
                d.module_id,
                d.tenant_id,
                d.source_uri,
                c.content,
                c.meta,
                1 - (c.embedding <=> $1::vector) AS similarity_score
            FROM rag.chunks c
            JOIN rag.documents d ON d.id = c.document_id
            WHERE {where_clause}
            ORDER BY c.embedding <=> $1::vector
            LIMIT {k}
        """
        rows = await self.db.fetch(query, *params)
        return [dict(r) for r in rows]
```

---

## 4. RAG Management UI (From FedTransform)

### 4.1 Capabilities to Extract

**From FedTransform backend:**
- ✅ `oracle_docs_crawler.py` - URL crawling with depth control
- ✅ `embedding_service.py` - Document embedding generation
- ✅ `background_embedding_service.py` - Async batch processing
- ✅ `content_chunker.py` - Intelligent text chunking
- ✅ `progress_tracker.py` - Ingestion progress tracking

### 4.2 New RAG Management Service

**Location:** `cortx-platform/services/rag_manager/`

**Purpose:** Centralized UI and API for managing all 4 levels of knowledge

**Features:**
```
RAG Management Dashboard:
├── Platform Knowledge
│   ├── Upload documents (PDF, DOCX, TXT, MD)
│   ├── Crawl URLs (with depth control)
│   ├── Import API documentation (OpenAPI specs)
│   └── View/search/delete embeddings
├── Suite Knowledge (per suite)
│   ├── Same capabilities as Platform
│   └── Suite admins can manage
├── Module Knowledge (per module)
│   ├── Same capabilities as Platform
│   └── Module owners can manage
└── Entity Knowledge (per tenant)
    ├── Same capabilities as Platform
    ├── Tenant-isolated (RLS enforced)
    └── Tenant admins can manage
```

**API Endpoints:**
```python
# RAG Management API
POST   /v1/rag/ingest                 # Ingest document/URL
GET    /v1/rag/knowledge               # List knowledge base
DELETE /v1/rag/knowledge/{id}          # Delete knowledge
POST   /v1/rag/search                  # Search knowledge base
GET    /v1/rag/progress/{job_id}       # Check ingestion progress

# Level-specific endpoints
POST   /v1/rag/platform/ingest
POST   /v1/rag/suites/{suite_id}/ingest
POST   /v1/rag/modules/{module_id}/ingest
POST   /v1/rag/tenants/{tenant_id}/ingest
```

### 4.3 UI Mockup

```typescript
// RAG Management Dashboard (Next.js)
export default function RAGManagementPage() {
  return (
    <DashboardLayout>
      <Tabs>
        <Tab label="Platform Knowledge">
          <KnowledgeIngestionForm level="platform" />
          <KnowledgeTable
            data={platformKnowledge}
            onDelete={handleDelete}
          />
        </Tab>

        <Tab label="Suite Knowledge">
          <SuiteSelector onChange={setSuite} />
          <KnowledgeIngestionForm
            level="suite"
            suiteId={selectedSuite}
          />
          <KnowledgeTable
            data={suiteKnowledge}
            onDelete={handleDelete}
          />
        </Tab>

        <Tab label="Module Knowledge">
          <ModuleSelector onChange={setModule} />
          <KnowledgeIngestionForm
            level="module"
            moduleId={selectedModule}
          />
          <KnowledgeTable
            data={moduleKnowledge}
            onDelete={handleDelete}
          />
        </Tab>

        <Tab label="My Organization">
          <KnowledgeIngestionForm
            level="entity"
            tenantId={currentTenantId}
          />
          <KnowledgeTable
            data={entityKnowledge}
            onDelete={handleDelete}
          />
        </Tab>
      </Tabs>
    </DashboardLayout>
  );
}

// Ingestion Form Component
function KnowledgeIngestionForm({ level, suiteId, moduleId, tenantId }) {
  return (
    <Card>
      <Tabs>
        <Tab label="Upload Document">
          <FileUpload
            accept=".pdf,.docx,.txt,.md"
            onUpload={handleUpload}
          />
        </Tab>

        <Tab label="Crawl URL">
          <URLCrawlerForm
            onSubmit={handleCrawl}
            options={{
              maxDepth: 3,
              maxPages: 100,
              excludePatterns: []
            }}
          />
        </Tab>

        <Tab label="Import API Docs">
          <OpenAPIImporter onImport={handleAPIImport} />
        </Tab>
      </Tabs>

      <IngestionProgress jobId={currentJobId} />
    </Card>
  );
}
```

---

## 5. OCR Service (Port 8137)

### 5.1 Service Purpose

Extract structured data from documents for all modules:
- **PropVerify**: Title documents, deeds, liens
- **FedTransform**: Legacy system reports, bank statements
- **ClaimsVerify** (MedSuite): Healthcare claims, EOBs
- **Any module**: PDF/image document processing

### 5.2 Architecture

**Technology Stack:**
- Tesseract OCR (open source)
- Google Document AI (production, high-accuracy)
- PyPDF2 for text-based PDFs
- OpenCV for image preprocessing

**Capabilities:**
```python
# services/ocr/app/main.py
from fastapi import FastAPI, UploadFile, File
from typing import Dict, Any, List

app = FastAPI(title="CORTX OCR Service", version="1.0.0")

@app.post("/v1/ocr/extract")
async def extract_text(
    file: UploadFile = File(...),
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract text from document

    Options:
    - engine: 'tesseract' | 'google_doc_ai' | 'auto'
    - language: 'eng', 'spa', etc.
    - preprocessing: enhance, denoise, deskew
    - output_format: 'text' | 'structured' | 'json'
    """
    pass

@app.post("/v1/ocr/extract-structured")
async def extract_structured_data(
    file: UploadFile = File(...),
    schema: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract structured data based on schema

    Example schema:
    {
      "fields": [
        {"name": "property_address", "type": "address"},
        {"name": "owner_name", "type": "person"},
        {"name": "parcel_id", "type": "alphanumeric"},
        {"name": "recording_date", "type": "date"}
      ]
    }
    """
    pass

@app.post("/v1/ocr/batch")
async def batch_extract(
    files: List[UploadFile],
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Batch process multiple documents
    Returns job_id for async processing
    """
    pass

@app.get("/v1/ocr/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check OCR job status"""
    pass
```

### 5.3 Data Linking (From PropVerify)

PropVerify has advanced `data_linker.py` (35K lines) that:
- Links extracted fields to master data
- Resolves ambiguities
- Cross-references multiple documents

**Decision:** Keep in PropVerify for now, extract if other modules need it.

---

## 6. Ledger Service (Port 8136)

### 6.1 Service Purpose

Provide immutable audit trails for compliance-critical operations:
- **PropVerify**: Title chain verification history
- **FedReconcile**: GTAS submission audit trail
- **ClaimsVerify**: Healthcare claims processing trail
- **Any module**: Tamper-proof audit logs

### 6.2 Architecture

**Technology:** Permissioned blockchain (Hyperledger Fabric or PostgreSQL with cryptographic hashing)

**MVP Approach (PostgreSQL-based):**

```python
# services/ledger/app/main.py
from fastapi import FastAPI, Depends
from typing import Dict, Any, List
import hashlib
import json
from datetime import datetime

app = FastAPI(title="CORTX Ledger Service", version="1.0.0")

@app.post("/v1/ledger/append")
async def append_entry(
    entry: Dict[str, Any],
    tenant_id: str,
    module_id: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Append immutable entry to ledger

    Entry structure:
    {
      "event_type": "title_verification_completed",
      "entity_id": "property_123",
      "entity_type": "property",
      "data_hash": "sha256_of_data",
      "metadata": {...},
      "timestamp": "2025-10-01T12:00:00Z"
    }

    Returns:
    {
      "ledger_entry_id": "uuid",
      "block_hash": "sha256_of_entry_+_prev_hash",
      "previous_block_hash": "...",
      "confirmation": "success"
    }
    """
    # Calculate hash chain
    prev_hash = await get_latest_block_hash(tenant_id)
    entry_with_prev = {**entry, "previous_hash": prev_hash}
    block_hash = hashlib.sha256(
        json.dumps(entry_with_prev, sort_keys=True).encode()
    ).hexdigest()

    # Store in ledger table
    await store_ledger_entry(
        tenant_id=tenant_id,
        module_id=module_id,
        user_id=user_id,
        entry=entry,
        block_hash=block_hash,
        previous_hash=prev_hash
    )

    return {
        "ledger_entry_id": "...",
        "block_hash": block_hash,
        "previous_block_hash": prev_hash,
        "confirmation": "success"
    }

@app.get("/v1/ledger/verify/{entry_id}")
async def verify_entry(entry_id: str) -> Dict[str, Any]:
    """
    Verify integrity of ledger entry
    Recalculates hash chain to ensure no tampering
    """
    pass

@app.get("/v1/ledger/history")
async def get_history(
    tenant_id: str,
    entity_id: str = None,
    module_id: str = None,
    start_date: str = None,
    end_date: str = None
) -> List[Dict[str, Any]]:
    """
    Get ledger history for entity/tenant
    """
    pass

@app.post("/v1/ledger/audit-report")
async def generate_audit_report(
    tenant_id: str,
    start_date: str,
    end_date: str,
    module_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Generate compliance audit report
    """
    pass
```

### 6.3 Database Schema

```sql
CREATE SCHEMA ledger;

CREATE TABLE ledger.blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(100) NOT NULL,
    module_id VARCHAR(100) NOT NULL,
    block_number BIGSERIAL,
    block_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256
    previous_hash VARCHAR(64),

    -- Entry data
    event_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255),
    entity_type VARCHAR(100),
    data_hash VARCHAR(64) NOT NULL,  -- Hash of actual data (stored separately)
    metadata JSONB,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,

    -- Constraints
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES platform.tenants(id),
    CONSTRAINT valid_hash_chain CHECK (
        (block_number = 1 AND previous_hash IS NULL) OR
        (block_number > 1 AND previous_hash IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_blocks_tenant ON ledger.blocks(tenant_id);
CREATE INDEX idx_blocks_entity ON ledger.blocks(tenant_id, entity_id);
CREATE INDEX idx_blocks_module ON ledger.blocks(module_id);
CREATE INDEX idx_blocks_created_at ON ledger.blocks(created_at);

-- Immutability: Prevent updates/deletes
REVOKE UPDATE, DELETE ON ledger.blocks FROM PUBLIC;
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
1. ✅ Design hierarchical RAG architecture (this document)
2. ⏳ Extract FedTransform RAG components
3. ⏳ Create RAG Management UI scaffold
4. ⏳ Set up pgvector database schema
5. ⏳ Implement basic retrieval (single-level)

### Phase 2: OCR & Ledger Services (Weeks 3-4)
1. ⏳ Extract PropVerify OCR engine
2. ⏳ Create OCR Service (port 8137)
3. ⏳ Extract PropVerify Ledger service
4. ⏳ Create Ledger Service (port 8136)
5. ⏳ Integrate services with AI Broker

### Phase 3: Hierarchical Retrieval (Weeks 5-6)
1. ⏳ Implement 4-level retrieval logic
2. ⏳ Build context scoring algorithm
3. ⏳ Add smart context expansion
4. ⏳ Performance optimization (caching, indexes)

### Phase 4: RAG Management UI (Weeks 7-8)
1. ⏳ Build document upload interface
2. ⏳ Build URL crawler interface
3. ⏳ Build knowledge browsing/search
4. ⏳ Implement progress tracking
5. ⏳ Add level-based permissions

### Phase 5: Integration & Testing (Weeks 9-10)
1. ⏳ Integrate with all suites
2. ⏳ Load initial knowledge bases
3. ⏳ End-to-end testing
4. ⏳ Performance tuning
5. ⏳ Documentation

---

## 8. Migration Strategy

### 8.1 Existing RAG Data

**FedTransform RAG data:**
- Current location: FedTransform embeddings (FAISS/local)
- Migration: Export → Re-embed → Import to Module-level (FedTransform)

**FedSuite RAG data:**
- Current location: `cortx-suites/fedsuite/embeddings/`
- Migration: Export → Categorize (Suite vs Module) → Import

### 8.2 Knowledge Seeding

**Platform Level (Week 1):**
- NIST 800-53 controls
- CORTX Platform docs
- General security best practices

**Suite Level (Week 2):**
- FedSuite: OMB circulars, GTAS guide, USSGL
- CorpSuite: Real estate law basics
- MedSuite: HIPAA regulations

**Module Level (Weeks 3-4):**
- FedTransform: Oracle/SAP schemas
- PropVerify: SDAT API docs
- FedReconcile: GTAS schemas

---

## 9. Open Questions & Decisions

### 9.1 Embedding Model
**Question:** Which embedding model?
- **Option A:** OpenAI `text-embedding-3-small` (384-dim, $0.02/1M tokens)
- **Option B:** Google `textembedding-gecko` (768-dim, Vertex AI pricing)
- **Option C:** Open source (Sentence Transformers, free, self-hosted)

**Recommendation:** Start with OpenAI (fast, cheap), migrate to open source for compliance/cost.

### 9.2 Chunking Strategy
**Question:** How to chunk documents?
- **Fixed size:** 512 tokens per chunk (simple)
- **Semantic chunking:** Split on paragraphs/sections (better context)
- **Hybrid:** Semantic + max size constraint

**Recommendation:** Semantic chunking with 512-token max.

### 9.3 Vector Store Performance
**Question:** Can pgvector handle this at scale?
- **Concern:** 1M+ embeddings across 4 levels
- **Alternative:** Pinecone, Weaviate, Qdrant (managed vector DBs)

**Recommendation:** Start with pgvector (simpler), monitor performance, migrate if needed.

---
 
**END OF DOCUMENT**

## 10. Environment & Deployment Considerations

**Environments:** `dev` → `staging` → `prod` with identical topology and promotion gates.

| Aspect | Dev | Staging | Prod |
|---|---|---|---|
| Identity | In-repo OIDC + GitHub/Google | Same + restricted external IdP | Keycloak/Auth0 or hardened OIDC |
| AI Providers | Vertex + (optional) OpenAI (flagged) | Vertex primary | Vertex only (unless ATO extends) |
| Database | Cloud SQL (HA in stg/prod) + pgvector | Cloud SQL (HA) + pgvector | Cloud SQL (HA) + pgvector |
| Redis | MemoryStore basic | MemoryStore standard | MemoryStore standard |
| Storage | gcs-{svc}-dev | gcs-{svc}-stg | gcs-{svc}-prod |
| Secrets | Secret Manager (dev) | Secret Manager (stg) | Secret Manager (prod) |
| Network | Private VPC (dev subnet) | Isolated subnet | Isolated subnet + WAF hardening |
| Deploy | Auto on main merge | Manual approve | Manual approve + change record |
| Data | Synthetic | Sanitized prod-like | Live tenant data |

**Demo Checkpoints** are aligned with this plan: (A) FedReconcile RAG demo (Week 3), (B) Ledger Evidence export (Week 6), (C) OCR→RAG pipeline (Week 8–9).
