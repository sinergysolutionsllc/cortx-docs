"""Audit utilities for CORTX services."""

import hashlib


def sha256_hex(data: str | bytes) -> str:
    """
    Compute SHA-256 hash of data and return as hex string.

    Args:
        data: String or bytes to hash

    Returns:
        Hexadecimal string representation of SHA-256 hash
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()
