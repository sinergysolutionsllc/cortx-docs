from __future__ import annotations

import hashlib
import hmac


def hmac_sha256(key: str | bytes, message: str | bytes) -> str:
    if isinstance(key, str):
        key_b = key.encode("utf-8")
    else:
        key_b = key
    if isinstance(message, str):
        msg_b = message.encode("utf-8")
    else:
        msg_b = message
    return hmac.new(key_b, msg_b, hashlib.sha256).hexdigest()
