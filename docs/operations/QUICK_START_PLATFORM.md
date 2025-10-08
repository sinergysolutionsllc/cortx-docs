# CORTX Platform - Quick Start Guide

## Overview

The CORTX Platform consists of two main parts:

### 1. Backend Services (Docker)

Microservices running in Docker containers providing core platform functionality.

### 2. Frontend Applications (Next.js)

React-based web applications for user interaction.

---

## Current Status

### ✅ What's Working

- Frontend applications can start (Designer, OffermAit, Suites, FedSuite)
- Backend service configuration exists
- Docker Compose setup is ready

### ❌ What's Missing

- Backend services are not running (Docker not started)
- Frontend apps are crashing due to missing backend services
- Database and cache infrastructure not initialized

---

## Complete Architecture

### Backend Services (Ports 8000-8999)

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Gateway** | 8080 | API Gateway, routing, rate limiting | ❌ Not Running |
| **Identity** | 8082 | Authentication, authorization, user management | ❌ Not Running |
| **Validation** | 8083 | Data validation, schema enforcement | ❌ Not Running |
| **AI Broker** | 8085 | AI/ML orchestration, Vertex AI integration | ❌ Not Running |
| **Workflow** | 8130 | Business process execution | ❌ Not Running |
| **Compliance** | 8135 | Compliance checking, rule validation | ❌ Not Running |
| **Ledger** | 8136 | Audit trail, immutable records | ❌ Not Running |
| **OCR** | 8137 | Document scanning, text extraction | ❌ Not Running |
| **RAG** | 8138 | Retrieval-Augmented Generation, knowledge base | ❌ Not Running |

### Infrastructure

| Component | Port | Purpose | Status |
|-----------|------|---------|--------|
| **PostgreSQL** (with pgvector) | 5432 | Primary database | ❌ Not Running |
| **Redis** | 6379 | Caching, session storage | ❌ Not Running |

### Frontend Applications (Ports 3000-3003)

| Application | Port | Purpose | Status |
|------------|------|---------|--------|
| **CORTX Designer** | 3000 | Visual workflow designer | ⚠️ Crashes without backend |
| **OffermAit** | 3001 | Offer management interface | ⚠️ Crashes without backend |
| **CORTX Suites** | 3002 | Main suite dashboard | ⚠️ Crashes without backend |
| **FedSuite** | 3003 | Federal compliance suite | ⚠️ Crashes without backend |

---

## Quick Start Instructions

### Prerequisites

1. **Docker Desktop** - Must be installed and running

   ```bash
   # Check if Docker is installed
   docker --version

   # Check if Docker is running
   docker info

   # If not running, start Docker Desktop
   open -a Docker
   ```

2. **Node.js** (v18+) - For frontend applications

   ```bash
   node --version
   npm --version
   ```

3. **GitHub CLI** - For cloning service repositories

   ```bash
   gh --version

   # If not installed
   brew install gh

   # Authenticate
   gh auth login
   ```

---

## Starting the Platform

### Option 1: Full Platform (Recommended)

Start everything at once (backend + frontend):

```bash
cd /Users/michael/Development/sinergysolutionsllc

# Start Docker Desktop first!
open -a Docker

# Wait for Docker to be ready, then:
./start-everything.sh
```

This will:

1. Clone/update all service repositories
2. Start backend services with Docker Compose
3. Wait for services to be healthy
4. Start frontend applications

### Option 2: Backend Only

If you only need backend services:

```bash
cd /Users/michael/Development/sinergysolutionsllc

./start-cortx.sh
```

### Option 3: Frontend Only

If backend is already running:

```bash
cd /Users/michael/Development/sinergysolutionsllc

./start-all.sh
```

---

## Checking Status

```bash
cd /Users/michael/Development/sinergysolutionsllc

./check-status.sh
```

This shows the health of all services and which are running.

---

## Stopping the Platform

### Stop Everything

```bash
cd /Users/michael/Development/sinergysolutionsllc

./stop-everything.sh
```

### Stop Backend Only

```bash
docker compose down
```

### Stop Frontend Only

```bash
# Find the PID
cat /tmp/cortx-frontends.pid

# Kill it
kill $(cat /tmp/cortx-frontends.pid)
```

---

## Accessing Services

### Frontend Applications

- **CORTX Designer**: <http://localhost:3000>
  - Visual workflow designer
  - BPM process creation

- **OffermAit**: <http://localhost:3001>
  - Offer management
  - AIT (Acquisition Information Tool)

- **CORTX Suites**: <http://localhost:3002>
  - Main dashboard
  - Suite management

- **FedSuite**: <http://localhost:3003>
  - Federal compliance tools
  - Regulatory workflows

### Backend APIs

All backend services expose:

- `GET /healthz` - Health check endpoint
- `GET /docs` - OpenAPI documentation (Swagger UI)
- `GET /openapi.json` - OpenAPI spec

Example:

- Gateway API Docs: <http://localhost:8080/docs>
- Identity API Docs: <http://localhost:8082/docs>

---

## Troubleshooting

### Docker Issues

**"Docker daemon not running"**

```bash
# Start Docker Desktop
open -a Docker

# Wait ~30 seconds, then verify
docker info
```

**"Cannot connect to Docker socket"**

```bash
# Reset Docker Desktop
# Docker Desktop > Settings > Troubleshoot > Reset to factory defaults
```

### Backend Services Not Starting

```bash
# Check Docker Compose logs
docker compose logs gateway
docker compose logs -f  # Follow all logs

# Check if containers are running
docker compose ps

# Restart a specific service
docker compose restart gateway

# Rebuild a service
docker compose up -d --build gateway
```

### Frontend Issues

**"Port already in use"**

```bash
# Find what's using the port
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or use the stop script
./stop-everything.sh
```

**"Module not found" errors**

```bash
# Reinstall dependencies
cd cortx-designer/frontend
npm install

# Or for all frontends
npm install  # From root (if using workspace)
```

**Canvas infinite loop fixed**
The React Flow infinite loop issue has been fixed in:

- `/Users/michael/Development/sinergysolutionsllc/packages/cortx-canvas/src/components/Canvas.tsx`

If you see the error again:

```bash
# Rebuild the canvas package
cd packages/cortx-canvas
npm run build
```

### Service Dependencies

Services have dependencies - start in this order:

1. Infrastructure (PostgreSQL, Redis)
2. Gateway
3. Identity, Validation
4. AI Broker
5. Workflow, Compliance, Ledger, OCR, RAG

Docker Compose handles this automatically with `depends_on`.

---

## Development Workflow

### Working on Backend Services

```bash
# Services are in ./repos/ directory after first run
cd repos/gateway

# Make changes, then rebuild
docker compose up -d --build gateway

# View logs
docker compose logs -f gateway
```

### Working on Frontend Applications

```bash
# Navigate to app
cd cortx-designer/frontend

# Start dev server manually (faster for development)
npm run dev

# Or edit and let start-all.sh handle it
```

### Working on Shared Packages

```bash
# Canvas package
cd packages/cortx-canvas

# Make changes
# ...

# Rebuild
npm run build

# Frontend apps will pick up changes automatically
```

---

## Environment Configuration

### Backend (.env)

Create `.env` in project root:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Security
JWT_SECRET_KEY=your_jwt_secret

# AI/ML
VERTEX_PROJECT_ID=your_gcp_project
VERTEX_LOCATION=us-central1

# Authentication
REQUIRE_AUTH=false  # Set true for production
```

### Frontend (.env.local)

Each frontend app can have its own `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_APP_VERSION=1.0.0
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `start-everything.sh` | Start all services (backend + frontend) |
| `start-cortx.sh` | Start backend services only |
| `start-all.sh` | Start frontend apps only |
| `stop-everything.sh` | Stop all services |
| `check-status.sh` | Show platform status |
| `bootstrap_sinergy.sh` | Initial setup script |

---

## Next Steps

1. **Start Docker Desktop**
2. **Run `./start-everything.sh`**
3. **Wait ~2 minutes** for all services to be healthy
4. **Open <http://localhost:3000>** (CORTX Designer)
5. **Check status** with `./check-status.sh`

---

## Getting Help

- **Logs**: Check `/tmp/cortx-frontends.log` for frontend logs
- **Backend Logs**: `docker compose logs -f [service]`
- **Status**: `./check-status.sh`
- **Docker Issues**: Check Docker Desktop logs
- **GitHub Issues**: Report issues to respective service repos

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Designer │  │OffermAit │  │  Suites  │  │FedSuite │ │
│  │  :3000   │  │  :3001   │  │  :3002   │  │  :3003  │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
└───────┼─────────────┼─────────────┼──────────────┼──────┘
        │             │             │              │
        └─────────────┴─────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │   Gateway   │ (:8080)
                    └──────┬──────┘
        ┌───────────┬──────┼──────┬───────────┬─────────┐
        │           │      │      │           │         │
   ┌────▼───┐  ┌───▼──┐ ┌─▼───┐ ┌▼────┐ ┌───▼───┐ ┌──▼──┐
   │Identity│  │Valid.│ │AI   │ │Work │ │Compli │ │ ... │
   │ :8082  │  │:8083 │ │:8085│ │:8130│ │ :8135 │ │     │
   └────┬───┘  └───┬──┘ └─────┘ └──┬──┘ └───┬───┘ └──┬──┘
        │          │                │        │        │
        └──────────┴────────────────┴────────┴────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼─────┐      ┌────▼────┐      ┌─────▼─────┐
   │PostgreSQL│      │  Redis  │      │ External  │
   │  :5432   │      │  :6379  │      │   APIs    │
   └──────────┘      └─────────┘      └───────────┘
```

---

**Last Updated**: 2025-10-07
