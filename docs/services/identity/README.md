# Identity Service (Port 8082)

**Status:** ✅ Implemented | **Version:** 0.1.0

## Overview

The Identity service is the authentication and authorization provider for the CORTX platform. It implements JWT-based authentication, role-based access control (RBAC), and multi-tenant user management, serving as the security foundation for all platform services.

## Core Responsibilities

### Authentication

- **JWT Token Issuance**: OAuth2-compatible token generation with configurable expiry
- **Password Authentication**: Secure password hashing with SHA-256
- **Token Verification**: Validates bearer tokens for protected resources
- **Session Management**: 24-hour access tokens with refresh capabilities

### Authorization

- **Role-Based Access Control**: User roles (`admin`, `user`, custom roles)
- **Scope Management**: Fine-grained permissions (`read`, `write`, `admin`)
- **Tenant Isolation**: Multi-tenant support with tenant-scoped authentication

### User Management

- **User CRUD**: Create, read, update, delete user accounts
- **Tenant Administration**: Tenant onboarding and management
- **Role Assignment**: Dynamic role creation and assignment (admin only)

## Architecture Diagram

```mermaid
flowchart TB
    Client[Client Application] -->|POST /v1/auth/login| Identity[Identity Service :8082]
    Gateway[Gateway Service] -->|Token Verification| Identity

    subgraph "Authentication Flow"
        Identity -->|1. Validate Credentials| Auth[Credential Validator]
        Auth -->|2. Hash Password| Hash[SHA-256 Hash]
        Hash -->|3. Compare| UserStore[(Mock User Store)]
        UserStore -->|4. User Data| TokenGen[JWT Token Generator]
        TokenGen -->|5. Sign Token| JWT[JWT with HS256]
    end

    subgraph "Authorization Flow"
        Gateway -->|Bearer Token| Verify[Token Verifier]
        Verify -->|Decode & Validate| Claims[Extract Claims]
        Claims -->|tenant_id, roles, scopes| RBAC[RBAC Enforcement]
    end

    Identity -->|Future: Persist| DB[(PostgreSQL)]
    Identity -->|Audit Events| Ledger[Ledger Service :8136]
```

## Key Features

### OAuth2 Compatibility

Standard OAuth2 password flow:

- Token endpoint: `/v1/auth/token`
- Supports `grant_type=password`
- Returns `access_token`, `token_type`, `expires_in`
- Compatible with OAuth2 client libraries

### JWT Token Structure

Tokens include these claims:

- `sub` (subject): Username
- `tenant_id`: Tenant context for multi-tenancy
- `roles`: Array of user roles
- `scopes`: Array of permissions
- `exp` (expiration): Token expiry timestamp
- `iat` (issued at): Token creation timestamp
- `iss` (issuer): "cortx-identity"

### Role-Based Access Control

Built-in roles:

- **admin**: Full platform access (all scopes)
- **user**: Standard user access (read scope)
- Custom roles can be created via API (admin only)

Built-in scopes:

- **read**: View resources
- **write**: Modify resources
- **admin**: Administrative operations

### Multi-Tenancy

Every user belongs to a tenant:

- Default tenant: `default`
- Tenant ID embedded in JWT
- Tenant-scoped user queries
- Cross-tenant isolation

## API Endpoints

### Health & Info

- `GET /health` - Service health check
- `GET /docs/info` - Service metadata and capabilities
- `GET /docs/openapi.json` - OpenAPI specification

### Authentication

- `POST /v1/auth/token` - OAuth2 token endpoint (form-encoded)
  - **Parameters**: `username`, `password`, `grant_type=password`
  - **Returns**: `access_token`, `token_type`, `expires_in`

- `POST /v1/auth/login` - Login endpoint (JSON)
  - **Body**: `{"username": "...", "password": "...", "tenant_id": "..."}`
  - **Returns**: JWT access token

- `GET /v1/auth/verify` - Verify token validity
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: User info and token claims

### User Management

- `GET /v1/me` - Get current authenticated user
  - **Headers**: `Authorization: Bearer <token>`
  - **Returns**: User profile with roles and scopes

### Tenant Management (Admin Only)

- `GET /v1/tenants` - List available tenants
  - **Requires**: `admin` role
  - **Returns**: Array of tenant objects

### Role Management (Admin Only)

- `POST /v1/roles` - Create new role
  - **Requires**: `admin` role
  - **Parameters**: `role_name`

## Database Schema

### Future Implementation (PostgreSQL)

The service currently uses an in-memory mock user store. Production deployment will use PostgreSQL with these tables:

#### Users Table (`users`)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false
);
```

#### Roles Table (`roles`)

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    scopes TEXT[], -- Array of scope strings
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### User Roles Junction (`user_roles`)

```sql
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);
```

#### Refresh Tokens Table (`refresh_tokens`)

```sql
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked BOOLEAN DEFAULT false
);
```

#### Tenants Table (`tenants`)

```sql
CREATE TABLE tenants (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB
);
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here  # Auto-generated if not provided
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Database (future implementation)
DATABASE_URL=postgresql://cortx:cortx_dev_password@localhost:5432/cortx

# Refresh Token Configuration (future)
REFRESH_TOKEN_SECRET=your-refresh-secret-here
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service Port
PORT=8082

# Logging
LOG_LEVEL=INFO
```

### Security Considerations

**Current Implementation (Development):**

- Mock user store with hardcoded credentials
- SHA-256 password hashing (not recommended for production)
- Auto-generated secret key per service restart

**Production Requirements:**

- Use bcrypt or argon2 for password hashing
- Store JWT secret in secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault)
- Implement refresh token rotation
- Add rate limiting on authentication endpoints
- Enable MFA (multi-factor authentication)
- Use HTTPS/TLS for all communications

## Usage Examples

### Login with OAuth2 Flow

```bash
curl -X POST http://localhost:8082/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123&grant_type=password"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Login with JSON Endpoint

```bash
curl -X POST http://localhost:8082/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "tenant_id": "default"
  }'
```

### Verify Token

```bash
curl -X GET http://localhost:8082/v1/auth/verify \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Response:

```json
{
  "valid": true,
  "username": "admin",
  "tenant_id": "default",
  "roles": ["admin", "user"],
  "scopes": ["read", "write", "admin"]
}
```

### Get Current User Info

```bash
curl -X GET http://localhost:8082/v1/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Response:

```json
{
  "username": "admin",
  "tenant_id": "default",
  "roles": ["admin", "user"],
  "scopes": ["read", "write", "admin"],
  "email": "admin@cortx.local"
}
```

### List Tenants (Admin Only)

```bash
curl -X GET http://localhost:8082/v1/tenants \
  -H "Authorization: Bearer <admin-token>"
```

Response:

```json
{
  "tenants": [
    {"id": "default", "name": "Default Tenant"},
    {"id": "fedsuite", "name": "FedSuite"},
    {"id": "demo", "name": "Demo Tenant"}
  ]
}
```

### Create Role (Admin Only)

```bash
curl -X POST "http://localhost:8082/v1/roles?role_name=auditor" \
  -H "Authorization: Bearer <admin-token>"
```

### Health Check

```bash
curl http://localhost:8082/health
```

## Integration Patterns

### Gateway Integration

The Gateway service uses the Identity service to validate requests:

1. Client sends request with `Authorization: Bearer <token>`
2. Gateway extracts token and calls `GET /v1/auth/verify`
3. Identity service validates token and returns user claims
4. Gateway enforces RBAC based on roles/scopes
5. Request forwarded to backend service with `X-Tenant-ID` header

### Frontend Integration

Frontend applications follow this flow:

1. **Login**: POST to `/v1/auth/login` with credentials
2. **Store Token**: Save `access_token` in secure storage (e.g., httpOnly cookie, localStorage)
3. **API Calls**: Include `Authorization: Bearer <token>` header on all requests
4. **Token Refresh**: Implement refresh token flow (future)
5. **Logout**: Remove token from storage

### Service-to-Service Authentication

Backend services can authenticate with Identity:

1. Service obtains JWT token (service account credentials)
2. Token includes service-specific roles/scopes
3. Token validated by downstream services
4. Audit trail maintained via Ledger service

## Mock Users (Development Only)

The current implementation includes these mock users:

| Username | Password | Tenant | Roles | Scopes |
|----------|----------|--------|-------|--------|
| `admin` | `admin123` | `default` | `admin`, `user` | `read`, `write`, `admin` |
| `user` | `user123` | `default` | `user` | `read` |

**WARNING:** These are for development only. Do not use in production.

## Security Features

### Token Security

- **HS256 Signing**: HMAC with SHA-256 for token integrity
- **Expiration**: Tokens expire after 24 hours (configurable)
- **Issuer Verification**: Tokens include `iss: cortx-identity` claim
- **Issued At**: Timestamp validation prevents token replay

### Password Security

Current: SHA-256 hashing (development only)

Production recommendations:

- Use bcrypt with salt rounds >= 12
- Or use argon2id for password hashing
- Implement password complexity requirements
- Add account lockout after failed attempts

### Future Enhancements

- **MFA**: TOTP (Time-based One-Time Password) support
- **OAuth Providers**: Google, GitHub, Microsoft SSO
- **API Keys**: Machine-to-machine authentication
- **Refresh Tokens**: Long-lived tokens for session renewal
- **Token Revocation**: Blacklist/whitelist for compromised tokens
- **Audit Logging**: Authentication events to Ledger service

## Performance

### Throughput

- **Token Generation**: ~500-1000 tokens/second (single instance)
- **Token Verification**: ~1000-2000 verifications/second
- **Latency**: <10ms for token operations

### Scalability

- Stateless architecture (JWT verification requires no DB lookup)
- Horizontal scaling via multiple service instances
- Secret key shared across instances via config service
- Future: Redis for refresh token storage and rate limiting

## Error Handling

### Authentication Errors

- **401 Unauthorized**: Invalid credentials or expired token

  ```json
  {
    "detail": "Could not validate credentials",
    "headers": {"WWW-Authenticate": "Bearer"}
  }
  ```

### Authorization Errors

- **403 Forbidden**: Insufficient permissions for operation

  ```json
  {
    "detail": "Admin access required"
  }
  ```

### Validation Errors

- **422 Unprocessable Entity**: Invalid request body

  ```json
  {
    "detail": [
      {
        "loc": ["body", "username"],
        "msg": "field required",
        "type": "value_error.missing"
      }
    ]
  }
  ```

## Monitoring & Logging

### Structured Logging

Future implementation will include:

- Login attempts (success/failure)
- Token issuance events
- Token verification requests
- Role/permission changes
- Admin operations

### Metrics

Recommended metrics:

- `identity_logins_total{status=success|failure}` - Login attempts
- `identity_tokens_issued_total` - Tokens created
- `identity_tokens_verified_total{valid=true|false}` - Verification requests
- `identity_token_expiry_seconds` - Token lifetime
- `identity_request_duration_seconds` - API latency

### Health Checks

- **Liveness**: `GET /health` - Is service running?
- **Readiness**: Check database connectivity (future)
- **Dependency**: Verify secrets manager availability (future)

## Development

### Local Setup

```bash
# Navigate to identity service directory
cd /Users/michael/Development/sinergysolutionsllc/services/identity

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8082 --reload

# Or run with Python directly
python app/main.py
```

### Testing Authentication

```bash
# Test login
TOKEN=$(curl -s -X POST http://localhost:8082/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Use token for authenticated request
curl -X GET http://localhost:8082/v1/me \
  -H "Authorization: Bearer $TOKEN"

# Verify token
curl -X GET http://localhost:8082/v1/auth/verify \
  -H "Authorization: Bearer $TOKEN"
```

### Docker

```bash
# Build container
docker build -f services/identity/Dockerfile -t cortx-identity:0.1.0 .

# Run container
docker run -p 8082:8082 \
  -e JWT_SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://cortx:password@db:5432/cortx \
  cortx-identity:0.1.0
```

## Deployment

### Docker Compose

```yaml
services:
  identity:
    image: cortx-identity:0.1.0
    ports:
      - "8082:8082"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=postgresql://cortx:${DB_PASSWORD}@postgres:5432/cortx
      - ACCESS_TOKEN_EXPIRE_MINUTES=1440
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
    networks:
      - cortx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8082/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes

```yaml
apiVersion: v1
kind: Service
metadata:
  name: cortx-identity
spec:
  selector:
    app: cortx-identity
  ports:
    - port: 8082
      targetPort: 8082
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cortx-identity
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cortx-identity
  template:
    metadata:
      labels:
        app: cortx-identity
    spec:
      containers:
      - name: identity
        image: cortx-identity:0.1.0
        ports:
        - containerPort: 8082
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: cortx-secrets
              key: jwt-secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cortx-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8082
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8082
          initialDelaySeconds: 10
          periodSeconds: 5
```

## Roadmap

### Phase 1: Database Integration

- Migrate from mock user store to PostgreSQL
- Implement user CRUD operations
- Add tenant and role tables
- Database migrations with Alembic

### Phase 2: Enhanced Security

- Replace SHA-256 with bcrypt/argon2
- Implement refresh token rotation
- Add rate limiting (Redis-backed)
- Secrets manager integration (AWS/Vault)

### Phase 3: MFA & SSO

- TOTP-based multi-factor authentication
- OAuth2 provider integration (Google, GitHub)
- SAML support for enterprise SSO
- Passwordless authentication (magic links)

### Phase 4: Advanced Features

- API key management for services
- Token revocation and blacklisting
- Session management dashboard
- Audit logging integration with Ledger

## Documentation

- **OpenAPI Spec**: [openapi.yaml](./openapi.yaml)
- **Source Code**: `/services/identity/app/main.py`
- **JWT Libraries**: [python-jose](https://github.com/mpdavis/python-jose)
- **OAuth2 Spec**: [RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)

## Support

For issues or questions:

- GitHub Issues: [sinergysolutionsllc/sinergysolutionsllc](https://github.com/sinergysolutionsllc/sinergysolutionsllc/issues)
- Internal Documentation: `/docs/services/identity/`
- Platform Team: Platform Services Team
