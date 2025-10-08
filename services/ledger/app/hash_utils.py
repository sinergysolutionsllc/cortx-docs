"""
Hash utilities for ledger chain
"""

import hashlib
import json
from typing import Any


def sha256_hex(data: Any) -> str:
    """
    Compute SHA-256 hash of data and return as hex string.

    Args:
        data: Data to hash (will be JSON serialized if not string)

    Returns:
        64-character hex string
    """
    if isinstance(data, str):
        content = data
    elif isinstance(data, bytes):
        content = data.decode("utf-8")
    else:
        # JSON serialize for consistent hashing
        content = json.dumps(data, sort_keys=True, separators=(",", ":"))

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_content_hash(event_data: dict) -> str:
    """
    Compute SHA-256 hash of event data.

    Args:
        event_data: Event data dictionary

    Returns:
        64-character hex string
    """
    return sha256_hex(event_data)


def compute_chain_hash(content_hash: str, previous_hash: str) -> str:
    """
    Compute chain hash from content hash and previous hash.

    Args:
        content_hash: SHA-256 hash of event content
        previous_hash: Previous event's chain hash

    Returns:
        64-character hex string
    """
    combined = content_hash + previous_hash
    return sha256_hex(combined)


# Genesis hash for first event in chain
GENESIS_HASH = "0" * 64
