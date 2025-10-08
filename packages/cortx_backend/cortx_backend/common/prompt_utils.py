from __future__ import annotations

import hmac
import json
import os
import re
from hashlib import sha256
from typing import Any


_SSN_RE = re.compile(r"\b(\d{3})[- ]?(\d{2})[- ]?(\d{4})\b")
_CC_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")


def strip_pii(text: str) -> str:
    """Best-effort PII scrubbing for prompts.

    - Masks SSNs: 123-45-6789 -> ***-**-6789
    - Masks likely credit card numbers: keep last 4 digits
    - Redacts emails and US phone numbers
    This is heuristic and should be augmented by platform services where available.
    """

    def _mask_ssn(m: re.Match[str]) -> str:
        return f"***-**-{m.group(3)}"

    def _mask_cc(m: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) < 8:
            return "[REDACTED-CC]"
        return f"[CC-**{digits[-4:]}]"

    text = _SSN_RE.sub(_mask_ssn, text)
    text = _CC_RE.sub(_mask_cc, text)
    text = _EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED-PHONE]", text)
    return text


def sha256_json(data: Any) -> str:
    """Deterministic SHA256 hash for JSON-serializable payloads."""
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(data, (bytes, bytearray)):
        payload = bytes(data)
    else:
        payload = str(data).encode("utf-8")
    return sha256(payload).hexdigest()


def hmac_sign(data: Any, *, key: str | None = None, timestamp: int | None = None) -> str:
    """Return HMAC-SHA256 signature hex of given data with optional timestamp.

    - Reads key from `PROMPT_HMAC_KEY` if not provided.
    - Data is JSON-normalized for determinism.
    - Optional timestamp for signature replay protection.
    """
    key = key if key is not None else os.getenv("PROMPT_HMAC_KEY", "")
    if not key:
        # Intentionally return a stable but empty-signature pattern rather than raising,
        # to avoid leaking secrets or breaking non-critical paths. Callers may enforce.
        return ""

    # Normalize data payload
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(data, (bytes, bytearray)):
        payload = bytes(data)
    else:
        payload = str(data).encode("utf-8")

    # Add timestamp if provided for replay protection
    if timestamp is not None:
        payload = f"{timestamp}:{payload.decode('utf-8')}".encode("utf-8")

    return hmac.new(key.encode("utf-8"), payload, sha256).hexdigest()


def verify_hmac_signature(data: Any, signature: str, *, key: str | None = None,
                         timestamp: int | None = None, max_age_seconds: int = 300) -> bool:
    """Verify HMAC signature of data.

    Args:
        data: The data to verify
        signature: The HMAC signature to verify against
        key: HMAC key (reads from PROMPT_HMAC_KEY if not provided)
        timestamp: Optional timestamp for replay protection
        max_age_seconds: Maximum age of signature in seconds (default 5 minutes)

    Returns:
        True if signature is valid and not too old, False otherwise
    """
    if not signature:
        return False

    key = key if key is not None else os.getenv("PROMPT_HMAC_KEY", "")
    if not key:
        return False

    # Check timestamp if provided
    if timestamp is not None:
        import time
        current_time = int(time.time())
        if current_time - timestamp > max_age_seconds:
            return False

    # Generate expected signature
    expected_signature = hmac_sign(data, key=key, timestamp=timestamp)

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


def generate_prompt_metadata(data: Any, *, include_timestamp: bool = True) -> dict:
    """Generate comprehensive metadata for prompt signing and audit.

    Args:
        data: The prompt data to generate metadata for
        include_timestamp: Whether to include timestamp for replay protection

    Returns:
        Dictionary with hash, signature, timestamp, and other metadata
    """
    import time

    timestamp = int(time.time()) if include_timestamp else None
    data_hash = sha256_json(data)
    signature = hmac_sign(data, timestamp=timestamp)

    metadata = {
        "data_hash": data_hash,
        "signature": signature,
        "algorithm": "HMAC-SHA256",
        "version": "1.0"
    }

    if timestamp:
        metadata["timestamp"] = timestamp
        metadata["expires_at"] = timestamp + 300  # 5 minutes default

    return metadata
