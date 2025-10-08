from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from .http_client import CORTXClient


class RAGClient:
    """Client for querying the CORTX RAG Compliance service."""

    def __init__(
        self,
        client: CORTXClient,
        cache_ttl_seconds: int | None = None,
    ) -> None:
        """
        Initializes the RAGClient.

        Args:
            client: An instance of CORTXClient for making HTTP requests.
            cache_ttl_seconds: The time-to-live for cache entries in seconds.
                               Defaults to RAG_CACHE_TTL env var or 86400.
        """
        self.client = client
        if cache_ttl_seconds is None:
            cache_ttl_seconds = int(os.getenv("RAG_CACHE_TTL", "86400"))
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}

    def _get_cache_key(self, query: str, context: str | None, regulations: List[str] | None) -> str:
        """Generate a deterministic cache key from the query parameters."""
        key_parts = [query]
        if context:
            key_parts.append(context)
        if regulations:
            key_parts.extend(sorted(regulations))
        # Use a hash to keep the key length manageable
        from hashlib import sha256
        return sha256("|".join(key_parts).encode()).hexdigest()

    def query(
        self,
        *,
        query: str,
        context: str | None = None,
        regulations: List[str] | None = None,
        correlation_id: str | None = None,
        traceparent: str | None = None,
    ) -> Dict[str, Any]:
        """
        Query the RAG service for compliance information.

        Args:
            query: The primary query string for the RAG system.
            context: Optional context, like a file path or code snippet.
            regulations: Optional list of regulations to scope the search (e.g., ["ALTA", "CFPB"]).
            correlation_id: Optional correlation ID for tracing.
            traceparent: Optional traceparent for distributed tracing.

        Returns:
            The JSON response from the RAG service.
        """
        # Check cache first
        cache_key = self._get_cache_key(query, context, regulations)
        if self.cache_ttl > 0 and cache_key in self._cache:
            response, timestamp = self._cache[cache_key]
            if (time.time() - timestamp) < self.cache_ttl:
                return response

        # If not in cache or expired, make the request
        payload: Dict[str, Any] = {"query": query}
        if context:
            payload["context"] = context
        if regulations:
            payload["regulations"] = regulations

        rag_response = self.client.post_json(
            "/compliance/rag/query",
            json=payload,
            correlation_id=correlation_id,
            traceparent=traceparent,
        )

        # Store in cache
        if self.cache_ttl > 0:
            self._cache[cache_key] = (rag_response, time.time())

        return rag_response
