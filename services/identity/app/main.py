"""
CORTX Identity Service - JWT-based authentication and authorization
"""

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jose import JWTError, jwt
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

app = FastAPI(title="CORTX Identity Service", version="0.1.0")
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")


# Models
class UserCredentials(BaseModel):
    username: str
    password: str
    tenant_id: str | None = "default"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: str
    tenant_id: str
    roles: list[str]
    scopes: list[str]


class User(BaseModel):
    username: str
    tenant_id: str
    roles: list[str]
    scopes: list[str]
    email: str | None = None


# Mock user store (replace with database in production)
MOCK_USERS = {
    "admin": {
        "password_hash": hashlib.sha256(b"admin123").hexdigest(),
        "tenant_id": "default",
        "roles": ["admin", "user"],
        "scopes": ["read", "write", "admin"],
        "email": "admin@cortx.local",
    },
    "user": {
        "password_hash": hashlib.sha256(b"user123").hexdigest(),
        "tenant_id": "default",
        "roles": ["user"],
        "scopes": ["read"],
        "email": "user@cortx.local",
    },
}


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == password_hash


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate user with username and password"""
    user = MOCK_USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "iss": "cortx-identity"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> TokenData:  # noqa: B008
    """Verify JWT token and return token data"""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id", "default")
        roles: list = payload.get("roles", [])
        scopes: list = payload.get("scopes", [])

        if username is None:
            raise credentials_exception

        return TokenData(username=username, tenant_id=tenant_id, roles=roles, scopes=scopes)
    except JWTError as e:
        raise credentials_exception from e


async def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:  # noqa: B008
    """Get current authenticated user"""
    return User(
        username=token_data.username,
        tenant_id=token_data.tenant_id,
        roles=token_data.roles,
        scopes=token_data.scopes,
    )


# Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "identity"}


@app.post("/v1/auth/token", response_model=Token)
async def create_token(form_data: OAuth2PasswordRequestForm = Depends()):  # noqa: B008
    """OAuth2 compatible token endpoint"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": form_data.username,
            "tenant_id": user["tenant_id"],
            "roles": user["roles"],
            "scopes": user["scopes"],
        },
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/v1/auth/login", response_model=Token)
async def login(credentials: UserCredentials):
    """Login endpoint (alternative to OAuth2 flow)"""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": credentials.username,
            "tenant_id": credentials.tenant_id or user["tenant_id"],
            "roles": user["roles"],
            "scopes": user["scopes"],
        },
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.get("/v1/auth/verify")
async def verify(token_data: TokenData = Depends(verify_token)):  # noqa: B008
    """Verify token and return user info"""
    return {
        "valid": True,
        "username": token_data.username,
        "tenant_id": token_data.tenant_id,
        "roles": token_data.roles,
        "scopes": token_data.scopes,
    }


@app.get("/v1/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):  # noqa: B008
    """Get current user info"""
    return current_user


@app.get("/v1/tenants")
async def get_tenants(current_user: User = Depends(get_current_user)):  # noqa: B008
    """Get available tenants (admin only)"""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "tenants": [
            {"id": "default", "name": "Default Tenant"},
            {"id": "fedsuite", "name": "FedSuite"},
            {"id": "demo", "name": "Demo Tenant"},
        ]
    }


@app.post("/v1/roles")
async def create_role(role_name: str, current_user: User = Depends(get_current_user)):  # noqa: B008
    """Create new role (admin only)"""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"message": f"Role {role_name} created", "role": role_name}


@app.get("/docs/openapi.json")
async def get_openapi_spec():
    """Get OpenAPI specification for this service"""
    try:
        openapi_path = Path(__file__).parent.parent / "openapi.json"
        with open(openapi_path) as f:
            openapi_spec = json.load(f)
        return JSONResponse(content=openapi_spec)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="OpenAPI specification not found") from e


@app.get("/docs/info")
async def get_service_info():
    """Get service information and capabilities"""
    return {
        "service": "identity",
        "version": "1.0.0",
        "title": "CORTX Identity Service",
        "description": "JWT-based authentication and authorization service",
        "capabilities": [
            "user_authentication",
            "jwt_token_management",
            "role_based_access_control",
            "multi_tenant_support",
        ],
        "endpoints": {
            "login": "/v1/auth/login",
            "verify": "/v1/auth/verify",
            "user_info": "/v1/me",
            "openapi": "/docs/openapi.json",
        },
    }


if __name__ == "__main__":
    import atexit
    import os
    import sys

    import uvicorn

    # Add shared path for port manager
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from shared.port_manager import get_port_manager

    # Get dynamic port
    port_manager = get_port_manager()
    port = port_manager.get_reserved_port("identity")

    # Register service
    port_manager.register_service(
        "identity",
        port,
        {
            "description": "JWT Authentication Service",
            "endpoints": ["/v1/auth/login", "/v1/auth/verify", "/v1/auth/user"],
        },
    )

    # Cleanup on exit
    atexit.register(lambda: port_manager.unregister_service("identity"))

    print(f"🔐 Identity Service starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
