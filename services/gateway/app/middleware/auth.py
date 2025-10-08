"""
JWT Authentication Middleware for CORTX Gateway
"""

import os

import httpx
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# Configuration
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8082")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Optional: for local validation
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """JWT Authentication middleware"""

    def __init__(self, identity_url: str = IDENTITY_SERVICE_URL):
        self.identity_url = identity_url
        self.client = httpx.AsyncClient()

    async def verify_token_remote(self, token: str) -> dict:
        """Verify token with identity service"""
        try:
            response = await self.client.get(
                f"{self.identity_url}/v1/auth/verify", headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None

    def verify_token_local(self, token: str) -> dict | None:
        """Verify token locally (if secret key is available)"""
        if not JWT_SECRET_KEY:
            return None

        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            return {
                "valid": True,
                "username": payload.get("sub"),
                "tenant_id": payload.get("tenant_id", "default"),
                "roles": payload.get("roles", []),
                "scopes": payload.get("scopes", []),
            }
        except JWTError:
            return None

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Security(security),  # noqa: B008
    ) -> dict | None:
        """Middleware to verify JWT tokens"""

        # Allow public endpoints
        if request.url.path in ["/health", "/", "/_info", "/docs", "/openapi.json"]:
            return None

        # Check for token
        if not credentials:
            # Check for token in cookie (for web UI)
            token = request.cookies.get("access_token")
            if not token:
                raise HTTPException(
                    status_code=401,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            token = credentials.credentials

        # Try local validation first (faster)
        user_info = self.verify_token_local(token)

        # Fall back to remote validation
        if not user_info:
            user_info = await self.verify_token_remote(token)

        if not user_info or not user_info.get("valid"):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Store user info in request state
        request.state.user = user_info
        request.state.tenant_id = user_info.get("tenant_id", "default")

        return user_info


# Singleton instance
auth_middleware = AuthMiddleware()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:  # noqa: B008
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_info = await auth_middleware.verify_token_remote(credentials.credentials)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_info


def require_role(role: str):
    """Dependency factory to require specific role"""

    async def role_checker(user: dict = Depends(get_current_user)):  # noqa: B008
        if role not in user.get("roles", []):
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return user

    return role_checker


def require_scope(scope: str):
    """Dependency factory to require specific scope"""

    async def scope_checker(user: dict = Depends(get_current_user)):  # noqa: B008
        if scope not in user.get("scopes", []):
            raise HTTPException(status_code=403, detail=f"Scope '{scope}' required")
        return user

    return scope_checker
