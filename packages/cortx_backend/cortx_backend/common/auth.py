from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

# Configuration from the CORTX Identity Service
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHMS", "HS256")

class JWTValidator:
    """Validates a symmetric JWT from the CORTX Identity Service."""

    def validate(self, token: str) -> Dict[str, Any]:
        if not SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not configured")

        try:
            claims = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
            )
            if not isinstance(claims, dict):
                raise ValueError("Claims are not a dictionary")
            return claims
        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def _extract_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]

def decode_token_optional(request: Request) -> Optional[Dict[str, Any]]:
    """Decode token if present; return None on absence or validation failure."""
    token = _extract_bearer_token(request)
    if not token:
        return None
    try:
        return JWTValidator().validate(token)
    except (HTTPException, RuntimeError):
        return None

def require_auth(request: Request) -> Dict[str, Any]:
    """Require a valid token and return its claims."""
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return JWTValidator().validate(token)


def require_roles(*roles: str):
    """Dependency to require specific roles from the token's claims."""
    roles_set = set(roles)

    def dep(claims: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
        claim_roles: List[str] = []
        for key in ("roles", "role", "permissions", "perms", "scope"):
            v = claims.get(key)
            if isinstance(v, list):
                claim_roles.extend([str(x) for x in v])
            elif isinstance(v, str):
                claim_roles.extend(v.split())

        if not roles_set.issubset(set(claim_roles)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return claims

    return dep

def get_user_id_from_claims(claims: Dict[str, Any]) -> Optional[str]:
    """Extracts a user identifier from standard JWT claims."""
    for k in ("sub", "preferred_username", "email", "uid"):
        v = claims.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def get_user_id_from_request(request: Request) -> Optional[str]:
    """Convenience function to get user ID from a request."""
    claims = decode_token_optional(request)
    if not claims:
        return None
    return get_user_id_from_claims(claims)
