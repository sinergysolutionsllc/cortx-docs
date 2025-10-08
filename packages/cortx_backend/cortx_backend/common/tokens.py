from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenProvider(Protocol):
    def get_token(self) -> str | None:
        ...


class EnvTokenProvider:
    """Simple token provider that reads a JWT from environment variables.

    This is a placeholder. In production, services should obtain a scoped JWT
    from CORTX Identity and refresh it as needed.
    """

    def __init__(self, env_var: str = "CORTX_JWT") -> None:
        self.env_var = env_var

    def get_token(self) -> str | None:
        token = os.getenv(self.env_var)
        if not token:
            # Fallback to a commonly used var name if present
            token = os.getenv("JWT")
        return token
