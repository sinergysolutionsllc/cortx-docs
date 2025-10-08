# CORTX Identity Service

FastAPI-based authentication and identity provider for the CORTX platform. It issues and verifies JWTs, manages tenants and users, and exposes endpoints for session refresh and user administration.

## Features

- `/v1/auth/login` and `/v1/auth/verify` JWT workflows
- Basic user CRUD under `/v1/users`
- Configurable token expiry and secrets via environment variables
- `/health` probe for liveness checks

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r services/identity/requirements.txt
uvicorn services.identity.app.main:app --reload --port 8082
```

The service expects access to its backing datastore (PostgreSQL) and configuration secrets. See `app/main.py` for the Pydantic settings model and default environment variables. Provide values such as `DATABASE_URL`, `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `REFRESH_TOKEN_SECRET` before running against real data.

## Docker

```bash
docker build -f services/identity/Dockerfile -t cortx-identity:local .
docker run --rm -p 8082:8082 cortx-identity:local \
  -e DATABASE_URL=postgresql://app:password@db:5432/identity \
  -e JWT_SECRET=changeme \
  -e REFRESH_TOKEN_SECRET=changeme
```

> The Dockerfile references runtime secrets and database connectivity that are supplied by the deployment environment. Update the build context once shared infrastructure modules are migrated.

## OpenAPI

`services/identity/openapi.yaml` contains the authoritative specification migrated from the legacy repository.

## TODO after migration

- Wire service into the shared Config Service once migrated
- Replace hard-coded defaults with references to the central secrets manager
- Add integration tests alongside gateway once the validation/identity workflow is ported

Maintainers: Platform Services Team.
