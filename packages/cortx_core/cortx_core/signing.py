from __future__ import annotations

import base64
import hmac
import json
import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol


@dataclass
class SignatureEnvelope:
    format: str  # e.g., DSSE-detached
    alg: str
    kid: str
    content_digest: str  # sha256 hex of canonicalized content
    payload_type: str
    signature_b64: str


class Signer(Protocol):
    def key_id(self) -> str: ...
    def alg(self) -> str: ...
    def sign_detached(
        self, content_digest: str, payload_type: str = "application/json"
    ) -> SignatureEnvelope: ...
    def verify_detached(self, envelope: SignatureEnvelope, content_digest: str) -> bool: ...


def canonicalize_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def content_sha256_hex(obj: dict) -> str:
    return sha256(canonicalize_json(obj).encode("utf-8")).hexdigest()


class FakeHMACSigner:
    def __init__(self, key: bytes, kid: str = "dev-fake-key"):
        self._key = key
        self._kid = kid

    def key_id(self) -> str:
        return self._kid

    def alg(self) -> str:
        return "HS256-FAKE"

    def sign_detached(
        self, content_digest: str, payload_type: str = "application/json"
    ) -> SignatureEnvelope:
        mac = hmac.new(self._key, content_digest.encode("utf-8"), sha256).digest()
        return SignatureEnvelope(
            format="DSSE-detached",
            alg=self.alg(),
            kid=self.key_id(),
            content_digest=content_digest,
            payload_type=payload_type,
            signature_b64=base64.b64encode(mac).decode("ascii"),
        )

    def verify_detached(self, envelope: SignatureEnvelope, content_digest: str) -> bool:
        if envelope.content_digest != content_digest:
            return False
        mac = hmac.new(self._key, content_digest.encode("utf-8"), sha256).digest()
        return hmac.compare_digest(base64.b64decode(envelope.signature_b64), mac)


class RSAPSSSigner:
    def __init__(self, private_key_pem: bytes, kid: str, public_key_pem: bytes | None = None):
        from cryptography.hazmat.primitives.serialization import (
            load_pem_private_key,
            load_pem_public_key,
        )

        self._priv = load_pem_private_key(private_key_pem, password=None)
        self._pub = load_pem_public_key(public_key_pem) if public_key_pem else None
        self._kid = kid

    def key_id(self) -> str:
        return self._kid

    def alg(self) -> str:
        return "RSASSA-PSS-SHA256"

    def sign_detached(
        self, content_digest: str, payload_type: str = "application/json"
    ) -> SignatureEnvelope:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        sig = self._priv.sign(
            content_digest.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return SignatureEnvelope(
            format="DSSE-detached",
            alg=self.alg(),
            kid=self.key_id(),
            content_digest=content_digest,
            payload_type=payload_type,
            signature_b64=base64.b64encode(sig).decode("ascii"),
        )

    def verify_detached(self, envelope: SignatureEnvelope, content_digest: str) -> bool:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.exceptions import InvalidSignature

        if not self._pub:
            return False
        if envelope.content_digest != content_digest:
            return False
        try:
            self._pub.verify(
                base64.b64decode(envelope.signature_b64),
                content_digest.encode("utf-8"),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False


def get_signer() -> Signer:
    mode = os.getenv("CORTX_SIGNING_MODE", "fake").lower()
    kid = os.getenv("CORTX_SIGNING_KEY_ID", "dev-fake-key")
    if mode == "rsa":
        priv_pem = os.getenv("CORTX_SIGNING_PRIVATE_KEY_PEM", "").encode("utf-8")
        pub_pem = os.getenv("CORTX_SIGNING_PUBLIC_KEY_PEM", "").encode("utf-8") or None
        if not priv_pem:
            raise RuntimeError("RSA signing mode requires CORTX_SIGNING_PRIVATE_KEY_PEM")
        return RSAPSSSigner(priv_pem, kid=kid, public_key_pem=pub_pem)
    # default: fake HMAC signer for dev
    key_b = (os.getenv("CORTX_FAKE_SIGNING_KEY") or "cortx-dev").encode("utf-8")
    return FakeHMACSigner(key=key_b, kid=kid)
