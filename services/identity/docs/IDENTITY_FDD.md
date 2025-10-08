# CORTX Identity Service - Functional Design Document

**Version**: 1.0.0
**Last Updated**: 2025-10-08
**Status**: Active

## 1. Purpose and Scope

### 1.1 Purpose

The CORTX Identity service provides centralized authentication, authorization, and identity management for the entire CORTX platform. It issues and verifies JWT tokens, manages users and tenants, and enforces role-based access control.

### 1.2 Scope

- User authentication (login/logout)
- JWT token issuance and verification
- User CRUD operations
- Tenant management
- Role-based access control (RBAC)
- Session management
- Token refresh workflows

### 1.3 Out of Scope

- OAuth2/OIDC provider integration (future phase)
- Multi-factor authentication (future phase)
- Password reset workflows (future phase)
- SSO integration (future phase)

## 2. Key Features

### 2.1 Authentication

- **Username/Password Login**: Traditional credentials-based authentication
- **JWT Token Issuance**: Access tokens (15 min) and refresh tokens (7 days)
- **Token Verification**: Validate JWT signatures and claims
- **Token Refresh**: Extend session without re-authentication

### 2.2 User Management

- **User CRUD**: Create, read, update, delete user accounts
- **Profile Management**: Users can update their own profiles
- **Role Assignment**: Admin can assign roles to users
- **Status Management**: Enable/disable user accounts

### 2.3 Authorization

- **Role-Based Access Control**: admin, user, readonly roles
- **Tenant Isolation**: Users belong to specific tenants
- **Permission Checking**: Verify user permissions for actions

## 3. API Contracts

### 3.1 Authentication Endpoints

#### Login

```
POST /v1/auth/login
Body:
  {
    "username": "string",
    "password": "string"
  }
Response: 200 OK
  {
    "access_token": "jwt_string",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "username": "string",
      "email": "string",
      "roles": ["admin"],
      "tenant_id": "string"
    }
  }
```

#### Verify Token

```
GET /v1/auth/verify
Headers:
  Authorization: Bearer {token}
Response: 200 OK
  {
    "valid": true,
    "user": {...}
  }
```

### 3.2 User Management Endpoints

#### List Users (Admin Only)

```
GET /v1/users?page=1&size=10
Response: 200 OK
  {
    "users": [...],
    "total": 100,
    "page": 1,
    "size": 10,
    "pages": 10
  }
```

#### Create User (Admin Only)

```
POST /v1/users
Body:
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "roles": ["user"],
    "tenant_id": "string"
  }
Response: 201 Created
  {
    "user": {...}
  }
```

#### Get User

```
GET /v1/users/{user_id}
Response: 200 OK
  {
    "user": {...}
  }
```

## 4. Dependencies

### 4.1 Upstream Dependencies

- **PostgreSQL Database**: User and session storage
- **Secret Manager**: JWT signing keys
- **Redis** (optional): Session caching

### 4.2 Downstream Consumers

- **Gateway Service**: Token verification
- **All CORTX Services**: Authentication
- **Frontend Applications**: User login

## 5. Data Models

### 5.1 User

```python
@dataclass
class User:
    id: UUID
    username: str
    email: str
    password_hash: str
    tenant_id: str
    roles: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
```

### 5.2 JWT Claims

```python
{
  "sub": "user_id",
  "username": "johndoe",
  "email": "john@example.com",
  "tenant_id": "tenant-123",
  "roles": ["admin"],
  "exp": 1234567890,
  "iat": 1234567800,
  "iss": "cortx-identity",
  "aud": "cortx-platform"
}
```

## 6. Configuration

### 6.1 Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | URL | Required | PostgreSQL connection string |
| `JWT_SECRET` | string | Required | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | 15 | Access token lifetime |
| `REFRESH_TOKEN_SECRET` | string | Required | Refresh token secret |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | 7 | Refresh token lifetime |
| `JWT_ALGORITHM` | string | HS256 | JWT signing algorithm |

## 7. Security Considerations

### 7.1 Password Security

- **Hashing**: bcrypt with cost factor 12
- **Salt**: Unique salt per password
- **Validation**: Minimum 8 characters, complexity rules

### 7.2 Token Security

- **Signing**: HMAC-SHA256 (HS256) or RS256
- **Expiration**: Short-lived access tokens
- **Refresh**: Separate refresh token with longer lifetime
- **Revocation**: Token blacklist for logout

### 7.3 Rate Limiting

- **Login Attempts**: 5 per minute per IP
- **Token Refresh**: 10 per minute per user
- **Account Lockout**: After 5 failed login attempts

## 8. Performance Characteristics

### 8.1 Latency Targets

- Login: < 200ms
- Token verification: < 50ms
- User CRUD: < 100ms

### 8.2 Throughput Targets

- 500 login requests/second
- 2000 token verifications/second

## 9. Monitoring and Observability

### 9.1 Metrics

- Login attempts (success/failure)
- Token issuance rate
- Token verification rate
- Active sessions
- Failed authentication attempts

### 9.2 Alerts

- High failed login rate (> 10% of attempts)
- Token verification failures
- Database connection issues
- Elevated error rates

## 10. Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-08 | Initial FDD creation |

## 11. References

- [OpenAPI Specification](../openapi.yaml)
- [Deployment Guide](./operations/deployment.md)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
