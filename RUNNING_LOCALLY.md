# Running CORTX Platform Locally

This guide explains how to run the entire CORTX platform on your local machine.

## Prerequisites

- **Docker** & **Docker Compose** - For containerized services
- **GitHub CLI (`gh`)** - For cloning private repos
- **8GB+ RAM** - To run all services simultaneously

Install prerequisites:
```bash
# macOS
brew install gh docker

# Authenticate with GitHub
gh auth login
```

## Quick Start (Automated)

The easiest way to run everything:

```bash
./start-cortx.sh
```

This script will:
1. ✅ Clone/update all service repositories to `./repos/`
2. ✅ Clone shared repos (cortx-platform, cortx-sdks)
3. ✅ Create `.env` from `.env.example` if needed
4. ✅ Build all Docker images
5. ✅ Start all services with health checks
6. ✅ Auto-restart failed services

## What Gets Started

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database with pgvector |
| Redis | 6379 | Cache & event bus |
| Gateway | 8080 | API Gateway |
| Identity | 8082 | Authentication |
| Validation | 8083 | Schema validation |
| AI Broker | 8085 | AI routing |
| Workflow | 8130 | Orchestration |
| Compliance | 8135 | Audit logs |
| Ledger | 8136 | Immutable chain |
| OCR | 8137 | Document extraction |
| RAG | 8138 | Retrieval |

## Manual Control

### Start services
```bash
docker compose up -d
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f validation
```

### Restart a service
```bash
docker compose restart validation
```

### Stop everything
```bash
docker compose down
```

### Rebuild a service
```bash
docker compose up -d --build validation
```

## Health Checks

Each service exposes health endpoints:

```bash
# Check if validation service is healthy
curl http://localhost:8083/healthz

# Check all services
for port in 8080 8082 8083 8085 8130 8135 8136 8137 8138; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/healthz || echo "FAILED"
done
```

## Troubleshooting

### Services keep restarting

Check logs for specific service:
```bash
docker compose logs validation
```

### Port conflicts

If ports are already in use, update `.env`:
```bash
GATEWAY_PORT=8180
IDENTITY_PORT=8182
# etc...
```

### Database connection issues

Reset database:
```bash
docker compose down -v  # Removes volumes
docker compose up -d
```

### Update service code

Pull latest changes and rebuild:
```bash
./start-cortx.sh  # Re-runs sync and rebuild
```

Or manually:
```bash
cd repos/validation
git pull
cd ../..
docker compose up -d --build validation
```

## Development Workflow

### Work on a single service locally

1. Stop the containerized version:
```bash
docker compose stop validation
```

2. Run locally for development:
```bash
cd repos/validation
pip install -e .
export CORTX_GATEWAY_URL=http://localhost:8080
export POSTGRES_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx
uvicorn app.main:app --reload --port 8083
```

3. When done, restart container:
```bash
docker compose start validation
```

### Add a new service

1. Add to `docker-compose.yml`
2. Add to `SERVICES` array in `start-cortx.sh`
3. Run `./start-cortx.sh`

## Self-Healing Features

The platform includes automatic recovery:

- **Health checks** - Services report `/healthz`, `/readyz`, `/livez`
- **Auto-restart** - Failed services restart automatically
- **Dependency ordering** - Services wait for dependencies (postgres, redis, gateway)
- **Graceful degradation** - Services continue if non-critical deps fail

## Architecture

```
┌─────────────────────────────────────────┐
│         Gateway (8080)                  │
│  ┌─────────┬─────────┬────────────┐   │
├──┤ Identity│Validation│ AI Broker  │   │
│  └─────────┴─────────┴────────────┘   │
│  ┌─────────┬─────────┬────────────┐   │
├──┤ Workflow│Compliance│  Ledger    │   │
│  └─────────┴─────────┴────────────┘   │
│  ┌─────────┬─────────┐                 │
├──┤   OCR   │   RAG   │                 │
│  └─────────┴─────────┘                 │
└──────────┬──────────┬──────────────────┘
           │          │
    ┌──────▼──┐   ┌───▼────┐
    │PostgreSQL│   │ Redis  │
    └──────────┘   └────────┘
```

All services import shared code from `cortx-platform/packages/cortx_core`.

## Next Steps

- Read [SERVICE_ARCHITECTURE.md](./SERVICE_ARCHITECTURE.md) for detailed design
- See individual service READMEs in `repos/[service]/`
- Configure production settings in `.env`
