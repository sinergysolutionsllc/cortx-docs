# Start All Services Guide

This guide explains how to start all frontend services and navigate between them.

## Frontend Services

### 1. CORTX Designer (BPM Workflow Designer)

- **Location**: `/Users/michael/Development/sinergysolutionsllc/cortx-designer/frontend`
- **Port**: 3000 (default)
- **URL**: <http://localhost:3000>
- **Main Routes**:
  - `/` - Home page
  - `/designer` - Visual workflow designer (main feature)
  - `/processes` - Process list

### 2. OffermAit (Investment Management)

- **Location**: `/Users/michael/Development/OffermAit/frontend`
- **Port**: 3000 (configured in package.json)
- **URL**: <http://localhost:3000>
- **Features**: Investment management UI

### 3. CORTX Suites (Suite Management)

- **Location**: `/Users/michael/Development/cortx-suites/frontend`
- **Port**: 3000 (default)
- **URL**: <http://localhost:3000>
- **Features**: Suite management UI

### 4. FedSuite (Federal Compliance Suite)

- **Location**: `/Users/michael/Development/sinergysolutionsllc/fedsuite/frontend`
- **Port**: 3000 (default)
- **URL**: <http://localhost:3000>
- **Features**: Federal compliance tools

## ⚠️ Port Conflict Issue

All services are configured to run on port 3000 by default, which will cause conflicts. You need to run them on different ports.

## Solution 1: Start Services on Different Ports (Recommended)

### Terminal 1 - CORTX Designer

```bash
cd /Users/michael/Development/sinergysolutionsllc/cortx-designer/frontend
npm run dev
# Runs on http://localhost:3000
```

### Terminal 2 - OffermAit

```bash
cd /Users/michael/Development/OffermAit/frontend
npm run dev -- -p 3001
# Runs on http://localhost:3001
```

### Terminal 3 - CORTX Suites

```bash
cd /Users/michael/Development/cortx-suites/frontend
npm run dev -- -p 3002
# Runs on http://localhost:3002
```

### Terminal 4 - FedSuite

```bash
cd /Users/michael/Development/sinergysolutionsllc/fedsuite/frontend
npm run dev -- -p 3003
# Runs on http://localhost:3003
```

## Solution 2: Use tmux/screen for Multiple Terminals

### Using tmux (if installed)

```bash
# Create new tmux session
tmux new -s sinergy

# Split into 4 panes (Ctrl+b then %)
# In each pane, run one of the services above

# Navigate between panes: Ctrl+b then arrow keys
# Detach: Ctrl+b then d
# Reattach: tmux attach -t sinergy
```

## Solution 3: One-Command Startup Script

I'll create a startup script that uses `concurrently` to run all services:

### Install concurrently (if not already installed)

```bash
npm install -g concurrently
```

### Use the startup script

```bash
cd /Users/michael/Development/sinergysolutionsllc
./start-all.sh
```

## Backend Services

If you also need backend services running:

### Workflow Service

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/workflow
python -m uvicorn app.main:app --reload --port 8004
# URL: http://localhost:8004
```

### Gateway Service

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/gateway
python -m uvicorn app.main:app --reload --port 8000
# URL: http://localhost:8000
```

### Compliance Service

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/compliance
python -m uvicorn app.main:app --reload --port 8001
# URL: http://localhost:8001
```

### Identity Service

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/identity
python -m uvicorn app.main:app --reload --port 8002
# URL: http://localhost:8002
```

### Validation Service

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/validation
python -m uvicorn app.main:app --reload --port 8003
# URL: http://localhost:8003
```

### RAG Service (ThinkTank)

```bash
cd /Users/michael/Development/sinergysolutionsllc

PYTHONPATH=packages/cortx_backend:services/rag \
PORT=8138 \
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx \
CORTX_GATEWAY_URL=http://localhost:8080 \
CORTX_AI_BROKER_URL=http://localhost:8085 \
/opt/homebrew/bin/python3.11 -m uvicorn services.rag.app.main:app \
  --host 0.0.0.0 \
  --port 8138 \
  --reload
# URL: http://localhost:8138
# Health: http://localhost:8138/health
```

**Prerequisites:**

- PostgreSQL with pgvector extension enabled
- Database: `cortx`
- User: `cortx` / Password: `cortx_dev_password`

**Setup PostgreSQL + pgvector:**

```bash
# Create database
createdb cortx

# Enable pgvector extension
psql cortx -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
psql cortx -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Ledger Service (Audit Trail)

```bash
cd /Users/michael/Development/sinergysolutionsllc/services/ledger

PORT=8136 \
POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx \
/opt/homebrew/bin/python3.11 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8136 \
  --reload
# URL: http://localhost:8136
# Health: http://localhost:8136/healthz
# Ready: http://localhost:8136/readyz
```

**Features:**

- Append-only event log with SHA-256 hash chaining
- Chain integrity verification
- Multi-tenant event isolation
- CSV export for audit trails

**API Endpoints:**

- `POST /append` - Append new event to ledger
- `GET /verify?tenant_id=X` - Verify chain integrity
- `GET /events?tenant_id=X` - List events
- `GET /export?tenant_id=X` - Export events as CSV

**Prerequisites:**

- Same PostgreSQL database as RAG service
- Uses same `cortx` database and credentials

## Navigation Between UIs

### Access Points

1. **CORTX Designer** - <http://localhost:3000>
   - Main workflow designer at `/designer`
   - Features: Node palette, canvas, properties panel, AI assistant, compilation

2. **OffermAit** - <http://localhost:3001>
   - Investment management interface

3. **CORTX Suites** - <http://localhost:3002>
   - Suite management dashboard

4. **FedSuite** - <http://localhost:3003>
   - Federal compliance tools

### Quick Links (when all running)

Open these URLs in your browser tabs:

- [CORTX Designer](http://localhost:3000/designer)
- [OffermAit](http://localhost:3001)
- [CORTX Suites](http://localhost:3002)
- [FedSuite](http://localhost:3003)

## Service Health Checks

Once all services are running, verify they're accessible:

```bash
# Frontend services
curl http://localhost:3000
curl http://localhost:3001
curl http://localhost:3002
curl http://localhost:3003

# Backend services (if running)
curl http://localhost:8000/healthz    # Gateway
curl http://localhost:8001/healthz    # Compliance
curl http://localhost:8002/healthz    # Identity
curl http://localhost:8003/healthz    # Validation
curl http://localhost:8004/healthz    # Workflow
curl http://localhost:8138/healthz    # RAG/ThinkTank
curl http://localhost:8136/healthz    # Ledger
```

## Stopping Services

### Individual Services

- Press `Ctrl+C` in each terminal

### tmux Session

```bash
tmux kill-session -t sinergy
```

### Script (if using startup script)

- Press `Ctrl+C` once to stop all services

## Development Workflow

### Typical Workflow

1. Start CORTX Designer first (main development focus)
2. Start backend services if testing integrations
3. Start other frontends as needed for cross-suite features

### Hot Reload

All services support hot reload - changes to code will automatically refresh the browser.

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :3000

# Kill the process
kill -9 <PID>
```

### Services Won't Start

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

## Environment Variables

### CORTX Designer

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: <http://localhost:8085>)
- `WORKFLOW_SERVICE_URL` - Workflow service URL (default: <http://localhost:8004>)

### Set in terminal

```bash
export NEXT_PUBLIC_API_URL=http://localhost:8000
export WORKFLOW_SERVICE_URL=http://localhost:8004
npm run dev
```

Or create `.env.local` files in each frontend directory.
