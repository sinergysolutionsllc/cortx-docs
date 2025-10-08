# ThinkTank Quick Start Guide

**Status:** ✅ Fully Functional - Ready to Test

---

## Current Status

All backend services are running and tested:

```bash
✅ PostgreSQL + pgvector (port 5432)
✅ Redis (port 6379)
✅ Gateway (port 8080)
✅ AI Broker (port 8085)
✅ RAG Service (port 8138) - HEALTHY
```

Knowledge base has 1 test document with 1 embedded chunk.

---

## Test the Backend (CLI)

### 1. Check Service Health

```bash
curl http://localhost:8138/readyz | python3 -m json.tool
```

Expected output:

```json
{
  "status": "ready",
  "database": "connected",
  "documents": 1,
  "chunks": 1,
  "embedding_model": "all-MiniLM-L6-v2"
}
```

### 2. Query the RAG Service

```bash
curl -X POST http://localhost:8138/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are NIST 800-53 access control requirements?",
    "tenant_id": "cortx-platform"
  }' | python3 -m json.tool
```

Expected output:

```json
{
  "query": "What are NIST 800-53 access control requirements?",
  "answer": "Mock AI received your prompt: ...",
  "chunks_used": 1,
  "document_sources": ["NIST 800-53 Access Control Sample"],
  "model": "gemini-1.5-flash (mock)",
  "tokens_used": 304,
  "cache_hit": false
}
```

### 3. Upload a New Document

```bash
curl -X POST http://localhost:8138/documents/upload \
  -F "file=@/path/to/your/document.pdf" \
  -F "title=Your Document Title" \
  -F "level=platform" \
  -F "description=Optional description" \
  -F "tenant_id=cortx-platform"
```

---

## Test the Frontend (UI)

### 1. Start FedSuite Frontend

```bash
cd fedsuite/frontend
npm run dev
```

### 2. Open Browser

```bash
open http://localhost:3000
```

### 3. Look for ThinkTank FAB

- Bottom-right corner of the page
- Pulsing brain icon with radiating rings
- Click to open mini-panel

### 4. Test Query

1. Click the ThinkTank FAB
2. Type: "What are NIST 800-53 access control requirements?"
3. Press Enter or click send
4. Verify response appears with document citations

### 5. Test Features

- ✅ Drag the panel around the screen
- ✅ Click "Expand" to go full-page (route: `/thinktank`)
- ✅ Try example queries (shown in panel)
- ✅ Test multi-line input (Shift+Enter)
- ✅ Close panel (X button or Escape key)

---

## Service Management

### View Logs

```bash
# All services
docker compose logs -f

# Just RAG service
docker compose logs -f rag

# Last 50 lines
docker compose logs rag --tail=50
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart just RAG
docker compose restart rag

# Rebuild and restart RAG after code changes
docker compose build rag && docker compose up rag -d
```

### Stop Services

```bash
# Stop all
docker compose stop

# Stop just RAG
docker compose stop rag
```

---

## Upload More Documents

### Upload NIST 800-53 PDF

```bash
curl -X POST http://localhost:8138/documents/upload \
  -F "file=@/path/to/NIST-800-53.pdf" \
  -F "title=NIST 800-53 Rev 5 Security Controls" \
  -F "level=platform" \
  -F "description=Federal security control baseline" \
  -F "tenant_id=cortx-platform"
```

### Upload FedRAMP Documentation

```bash
curl -X POST http://localhost:8138/documents/upload \
  -F "file=@/path/to/FedRAMP-Controls.pdf" \
  -F "title=FedRAMP Security Controls" \
  -F "level=platform" \
  -F "suite_id=fedsuite" \
  -F "description=FedRAMP compliance requirements" \
  -F "tenant_id=cortx-platform"
```

### Upload Suite-Specific Docs

```bash
curl -X POST http://localhost:8138/documents/upload \
  -F "file=@/path/to/DataFlow-Guide.md" \
  -F "title=DataFlow User Guide" \
  -F "level=module" \
  -F "suite_id=fedsuite" \
  -F "module_id=dataflow" \
  -F "description=DataFlow module documentation" \
  -F "tenant_id=cortx-platform"
```

---

## Verify Document Upload

### List All Documents

```bash
curl http://localhost:8138/documents | python3 -m json.tool
```

### Check Knowledge Base Stats

```bash
curl http://localhost:8138/readyz | python3 -m json.tool
```

### Test Retrieval (Without LLM)

```bash
curl -X POST http://localhost:8138/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "access control",
    "tenant_id": "cortx-platform",
    "top_k": 5
  }' | python3 -m json.tool
```

---

## Configure Real AI (Optional)

Currently using mock AI responses. To enable real Gemini:

### 1. Set Up Google Cloud Credentials

```bash
# Set environment variables
export VERTEX_PROJECT_ID="your-gcp-project-id"
export VERTEX_LOCATION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### 2. Update Docker Compose

Edit `docker-compose.yml`:

```yaml
ai-broker:
  environment:
    - VERTEX_PROJECT_ID=${VERTEX_PROJECT_ID}
    - VERTEX_LOCATION=${VERTEX_LOCATION:-us-central1}
    - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
  volumes:
    - ${GOOGLE_APPLICATION_CREDENTIALS}:/app/credentials.json:ro
```

### 3. Restart AI Broker

```bash
docker compose restart ai-broker
```

### 4. Test with Real AI

```bash
curl -X POST http://localhost:8138/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain NIST 800-53 access control requirements in detail",
    "tenant_id": "cortx-platform"
  }' | python3 -m json.tool
```

---

## Troubleshooting

### RAG Service Not Responding

```bash
# Check if running
docker compose ps rag

# View logs
docker compose logs rag --tail=100

# Restart
docker compose restart rag
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker compose ps postgres

# Test connection from RAG container
docker exec cortx-rag psql postgresql://cortx:cortx_dev_password@postgres:5432/cortx -c "SELECT 1"

# Check tables
docker exec cortx-postgres psql -U cortx -d cortx -c "\dt rag.*"
```

### Port Already in Use

```bash
# Check what's using port 8138
lsof -ti:8138

# Kill the process
lsof -ti:8138 | xargs kill -9

# Restart RAG service
docker compose up rag -d
```

### Documents Not Being Retrieved

```bash
# Verify documents exist
curl http://localhost:8138/documents

# Check chunk count
curl http://localhost:8138/readyz

# Test direct retrieval
curl -X POST http://localhost:8138/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"test","tenant_id":"cortx-platform","top_k":10}'
```

---

## Next Steps

1. ✅ Backend is fully functional
2. ⏳ Start FedSuite frontend and test UI
3. ⏳ Upload production documents (NIST, FedRAMP, HIPAA)
4. ⏳ Configure real Gemini API (optional)
5. ⏳ Deploy to other suites (CorpSuite, MedSuite, GovSuite)

---

## Quick Reference

| Component | Port | URL | Status |
|-----------|------|-----|--------|
| FedSuite | 3000 | <http://localhost:3000> | ⏳ Not started |
| Gateway | 8080 | <http://localhost:8080> | ✅ Running |
| AI Broker | 8085 | <http://localhost:8085> | ✅ Running |
| **RAG Service** | **8138** | **<http://localhost:8138>** | **✅ Healthy** |
| PostgreSQL | 5432 | localhost:5432 | ✅ Running |
| Redis | 6379 | localhost:6379 | ✅ Running |

---

## Key Files

- **Documentation:** `THINKTANK_COMPLETION_SUMMARY.md` (full details)
- **Status Report:** `THINKTANK_IMPLEMENTATION_STATUS.md` (progress tracking)
- **Frontend Integration:** `fedsuite/THINKTANK_INTEGRATION_SUMMARY.md`
- **Backend Code:** `services/rag/app/main.py`
- **Database Models:** `services/rag/app/models.py`
- **UI Components:** `packages/cortx-ui/src/components/thinktank/`

---

**Last Updated:** October 7, 2025, 4:30 PM EDT
**Ready for:** Demo and Frontend Testing
