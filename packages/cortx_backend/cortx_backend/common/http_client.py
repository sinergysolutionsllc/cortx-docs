from __future__ import annotations

import time
import uuid
from typing import Any

import httpx

from .config import CORTXConfig
from .tokens import TokenProvider

TRANSIENT_STATUS = {429, 500, 502, 503, 504}


class CORTXClient:
    """HTTP client for calling CORTX services through the Gateway.

    - Injects Authorization, X-Correlation-ID, and traceparent headers.
    - Applies basic retries with exponential backoff on transient errors.
    - Uses a base URL (Gateway) and relative paths per call.
    """

    def __init__(
        self,
        config: CORTXConfig,
        token_provider: TokenProvider,
        *,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        client: httpx.Client | None = None,
    ) -> None:
        if not config.gateway_url:
            raise ValueError("CORTX_GATEWAY_URL must be configured")
        self.base_url = config.gateway_url.rstrip("/")
        self.token_provider = token_provider
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def _build_headers(
        self,
        *,
        correlation_id: str | None,
        traceparent: str | None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        headers: dict[str, str] = {}
        token = self.token_provider.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        headers["X-Correlation-ID"] = correlation_id or str(uuid.uuid4())
        if traceparent:
            headers["traceparent"] = traceparent
        if extra:
            headers.update(extra)
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        correlation_id: str | None = None,
        traceparent: str | None = None,
        json: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = self._build_headers(
            correlation_id=correlation_id, traceparent=traceparent, extra=headers
        )
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._client.request(
                    method=method.upper(), url=url, json=json, params=params, headers=req_headers
                )
            except httpx.HTTPError:
                if attempt <= self.max_retries:
                    time.sleep(self.backoff_factor * attempt)
                    continue
                raise
            if resp.status_code in TRANSIENT_STATUS and attempt <= self.max_retries:
                time.sleep(self.backoff_factor * attempt)
                continue
            return resp

    def get_json(
        self,
        path: str,
        *,
        correlation_id: str | None = None,
        traceparent: str | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        resp = self.request(
            "GET",
            path,
            correlation_id=correlation_id,
            traceparent=traceparent,
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def post_json(
        self,
        path: str,
        *,
        correlation_id: str | None = None,
        traceparent: str | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        resp = self.request(
            "POST",
            path,
            correlation_id=correlation_id,
            traceparent=traceparent,
            json=json,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
