from __future__ import annotations

import os
from typing import Optional

from .http_client import CORTXClient
from .prompt_utils import strip_pii


def redact_text(
    text: str,
    *,
    client: Optional[CORTXClient] = None,
    correlation_id: Optional[str] = None,
    traceparent: Optional[str] = None,
) -> str:
    """Redact prompt text using CORTX Gateway if enabled; otherwise fallback to local rules.

    Env flags:
    - USE_CORTX_REDACTION=true|false (default false)
    - CORTX_PII_REDACT_PATH (default '/pii/redact')
    """
    use_gateway = os.getenv("USE_CORTX_REDACTION", "false").lower() in {"1", "true", "yes"}
    if use_gateway and client is not None:
        try:
            path = os.getenv("CORTX_PII_REDACT_PATH", "/pii/redact")
            resp = client.post_json(
                path,
                correlation_id=correlation_id,
                traceparent=traceparent,
                json={"text": text},
            )
            redacted = resp.get("text")
            if isinstance(redacted, str) and redacted:
                return redacted
        except Exception:
            # Fall back to local redaction
            pass
    return strip_pii(text)
