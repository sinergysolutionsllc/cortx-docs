# CORTX Gateway Service

FastAPI reverse proxy that fronts the entire CORTX platform. Responsibilities:

- Terminate incoming requests and enforce auth policies
- Route traffic to orchestration endpoints, suite proxies, and service discovery APIs
- Broker RulePack validation requests via the policy router and registry client
- Provide health/_info probes used by installers and CI

## Local development

```bash
# Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r services/gateway/requirements.txt

# Run the dev server
python services/gateway/app/dev_main.py
```

The service expects supporting packages (`cortx_core`, `cortx_rulepack_sdk`, `cortx_recon`) to be installed in editable mode. Until those packages are migrated into the monorepo, install them from the legacy repositories or use the Docker workflow below.

## Docker

```bash
# Build the container (requires packages/ + modules/ once migrated)
docker build -f services/gateway/Dockerfile -t cortx-gateway:local .

# Run locally
docker run --rm -p 8080:8080 cortx-gateway:local
```

> Note: The Dockerfile still references shared packages that will be moved into the monorepo in later phases. Update the build context once those packages land.

## Endpoints

- `GET /health` – liveness probe
- `GET /_info` – metadata about enabled routers and features
- `POST /orchestrator/*` – primary orchestration API
- `GET /services` – service discovery helper
- Suite proxies (`/analytics`, `/recon`, `/fedsuite`, `/propverify`) for backward compatibility

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `CORTX_REGISTRY_URL` | RulePack registry service URL | `http://localhost:8081` |
| `CORTX_ENV` | Environment label consumed by logging | `dev` |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowlist | `http://localhost:3000,http://127.0.0.1:3000` |

Logging, registry connection details, and default CORS rules also pull from `cortx_core.config.settings` when available.

---

Maintainers: Platform Services Team.
