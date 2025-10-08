"""
RulePack Client

Client for calling remote RulePacks from CORTX orchestrator.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any

import httpx
from pydantic import BaseModel, Field

from cortx_rulepack_sdk.contracts import (
    ExplanationRequest,
    ExplanationResponse,
    RulePackInfo,
    RulePackMetadata,
    ValidationFailure,
    ValidationRequest,
    ValidationResponse,
)

logger = logging.getLogger(__name__)


class RulePackEndpoint(BaseModel):
    """Configuration for a RulePack endpoint"""

    url: str = Field(..., description="Base URL of the RulePack service")
    timeout: int = Field(default=300, description="Timeout in seconds")
    retries: int = Field(default=3, description="Number of retries")
    headers: dict[str, str] = Field(default_factory=dict)
    auth_token: str | None = Field(default=None, description="Bearer token for auth")


class RulePackClient:
    """
    Client for communicating with remote RulePack services.

    This is used by CORTX orchestrator to call individual RulePacks.
    """

    def __init__(self, endpoint: str | RulePackEndpoint):
        """
        Initialize client for a RulePack endpoint.

        Args:
            endpoint: Either URL string or RulePackEndpoint config
        """
        if isinstance(endpoint, str):
            self.endpoint = RulePackEndpoint(url=endpoint)
        else:
            self.endpoint = endpoint

        self._client: httpx.AsyncClient | None = None
        self._info_cache: RulePackInfo | None = None
        self._metadata_cache: RulePackMetadata | None = None
        self._cache_expiry: datetime | None = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize HTTP client connection"""
        if self._client is None:
            headers = self.endpoint.headers.copy()
            if self.endpoint.auth_token:
                headers["Authorization"] = f"Bearer {self.endpoint.auth_token}"

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.endpoint.timeout), headers=headers, follow_redirects=True
            )
            logger.debug(f"Connected to RulePack at {self.endpoint.url}")

    async def disconnect(self) -> None:
        """Close HTTP client connection"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug(f"Disconnected from RulePack at {self.endpoint.url}")

    def _is_cache_valid(self) -> bool:
        """Check if cached metadata is still valid"""
        return self._cache_expiry is not None and datetime.utcnow() < self._cache_expiry

    def _update_cache_expiry(self) -> None:
        """Update cache expiry to 5 minutes from now"""
        self._cache_expiry = datetime.utcnow() + timedelta(minutes=5)

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """
        Make HTTP request with retries.

        Args:
            method: HTTP method
            path: API path (without leading slash)
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: For HTTP errors
            httpx.RequestError: For connection errors
        """
        if not self._client:
            await self.connect()

        url = f"{self.endpoint.url.rstrip('/')}/{path.lstrip('/')}"

        for attempt in range(self.endpoint.retries + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")

                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()

                return response.json()

            except httpx.RequestError as e:
                if attempt == self.endpoint.retries:
                    logger.error(f"Request failed after {self.endpoint.retries + 1} attempts: {e}")
                    raise

                wait_time = 2**attempt  # Exponential backoff
                logger.warning(
                    f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)

            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"Client error {e.response.status_code}: {e}")
                    raise

                # Retry on server errors (5xx)
                if attempt == self.endpoint.retries:
                    logger.error(f"Server error after {self.endpoint.retries + 1} attempts: {e}")
                    raise

                wait_time = 2**attempt
                logger.warning(
                    f"Server error (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)

    async def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Call RulePack validation endpoint.

        Args:
            request: Validation request

        Returns:
            ValidationResponse from the RulePack
        """
        response_data = await self._request("POST", "validate", json=request.model_dump())

        return ValidationResponse.model_validate(response_data)

    async def validate_stream(self, request: ValidationRequest) -> AsyncIterator[ValidationFailure]:
        """
        Stream validation failures from RulePack.

        Args:
            request: Validation request

        Yields:
            ValidationFailure objects as they are discovered
        """
        # For now, fall back to batch validation
        # TODO: Implement true streaming via Server-Sent Events or WebSocket
        response = await self.validate(request)
        for failure in response.failures:
            yield failure

    async def explain(self, request: ExplanationRequest) -> ExplanationResponse:
        """
        Get explanation for a validation failure.

        Args:
            request: Explanation request

        Returns:
            ExplanationResponse from the RulePack
        """
        response_data = await self._request("POST", "explain", json=request.model_dump())

        return ExplanationResponse.model_validate(response_data)

    async def get_info(self, use_cache: bool = True) -> RulePackInfo:
        """
        Get RulePack information.

        Args:
            use_cache: Whether to use cached info

        Returns:
            RulePackInfo
        """
        if use_cache and self._info_cache and self._is_cache_valid():
            return self._info_cache

        response_data = await self._request("GET", "info")
        info = RulePackInfo.model_validate(response_data)

        self._info_cache = info
        self._update_cache_expiry()

        return info

    async def get_metadata(self, use_cache: bool = True) -> RulePackMetadata:
        """
        Get detailed RulePack metadata.

        Args:
            use_cache: Whether to use cached metadata

        Returns:
            RulePackMetadata
        """
        if use_cache and self._metadata_cache and self._is_cache_valid():
            return self._metadata_cache

        response_data = await self._request("GET", "metadata")
        metadata = RulePackMetadata.model_validate(response_data)

        self._metadata_cache = metadata
        self._update_cache_expiry()

        return metadata

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check of the RulePack.

        Returns:
            Health check response
        """
        return await self._request("GET", "health")

    def clear_cache(self) -> None:
        """Clear cached info and metadata"""
        self._info_cache = None
        self._metadata_cache = None
        self._cache_expiry = None
