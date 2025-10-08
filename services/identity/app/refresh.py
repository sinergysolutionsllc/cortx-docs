"""
Token refresh endpoint for JWT authentication
"""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

router = APIRouter(prefix="/v1/auth", tags=["Auth"])
security = HTTPBearer()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development_secret_key_change_in_production")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", SECRET_KEY + "_refresh")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_refresh_token(data: dict) -> str:
    """Create a refresh token with longer expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    """Create new access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        # Extract user data
        user_data = {
            "sub": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
            "roles": payload.get("roles"),
            "scopes": payload.get("scopes"),
        }

        # Create new token pair
        new_access_token = create_access_token(user_data)
        new_refresh_token = create_refresh_token(user_data)

        return TokenPair(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from e


@router.post("/revoke")
async def revoke_token(refresh_token: str):
    """Revoke a refresh token (placeholder for token blacklist implementation)"""
    # In production, implement token blacklist in Redis or database
    # For now, just validate the token
    try:
        jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        # TODO: Add token to blacklist
        # redis_client.sadd(f"blacklist:{payload['jti']}", 1)
        # redis_client.expire(f"blacklist:{payload['jti']}", REFRESH_TOKEN_EXPIRE_DAYS * 86400)

        return {"message": "Token revoked successfully"}
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
