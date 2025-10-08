"""
RulePack Registry Client

Client for registering and discovering RulePacks in the CORTX registry.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from cortx_rulepack_sdk.contracts import RulePackInfo

logger = logging.getLogger(__name__)


class RulePackStatus(str, Enum):
    """RulePack registration status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    MAINTENANCE = "maintenance"


class RulePackRegistration(BaseModel):
    """RulePack registration record"""

    domain: str = Field(..., description="Domain identifier (gtas, grants, etc.)")
    name: str = Field(..., description="RulePack name")
    version: str = Field(..., description="RulePack version")
    endpoint_url: str = Field(..., description="RulePack service URL")
    status: RulePackStatus = Field(default=RulePackStatus.ACTIVE)

    # Metadata
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    author: str | None = None

    # Health and monitoring
    health_check_url: str | None = Field(default=None, description="Health check endpoint")
    last_health_check: datetime | None = None
    health_status: str | None = None

    # Registration tracking
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    registered_by: str | None = None

    # Configuration
    timeout: int = Field(default=300, description="Request timeout in seconds")
    retries: int = Field(default=3, description="Number of retries")
    auth_required: bool = Field(default=False)

    # Capabilities from RulePackInfo
    supported_modes: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegistryClient:
    """
    Client for interacting with the CORTX RulePack Registry.

    The registry tracks all available RulePacks, their endpoints, versions,
    and health status.
    """

    def __init__(self, registry_url: str, auth_token: str | None = None):
        """
        Initialize registry client.

        Args:
            registry_url: Base URL of the registry service
            auth_token: Optional bearer token for authentication
        """
        self.registry_url = registry_url.rstrip("/")
        self.auth_token = auth_token
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize HTTP client"""
        if self._client is None:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            self._client = httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True)
            logger.debug(f"Connected to registry at {self.registry_url}")

    async def disconnect(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("Disconnected from registry")

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make HTTP request to registry"""
        if not self._client:
            await self.connect()

        url = f"{self.registry_url}/{path.lstrip('/')}"

        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()

            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return response.text

        except httpx.HTTPError as e:
            logger.error(f"Registry request failed: {method} {url} - {e}")
            raise

    async def register(self, registration: RulePackRegistration) -> dict[str, Any]:
        """
        Register a RulePack in the registry.

        Args:
            registration: RulePack registration details

        Returns:
            Registration confirmation
        """
        logger.info(
            f"Registering RulePack {registration.domain}:{registration.name}:{registration.version}"
        )

        response = await self._request("POST", "rulepacks", json=registration.model_dump())

        logger.info(f"Successfully registered RulePack {registration.domain}:{registration.name}")
        return response

    async def update(self, domain: str, name: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update a RulePack registration.

        Args:
            domain: RulePack domain
            name: RulePack name
            updates: Fields to update

        Returns:
            Update confirmation
        """
        logger.info(f"Updating RulePack {domain}:{name}")

        response = await self._request("PATCH", f"rulepacks/{domain}/{name}", json=updates)

        logger.info(f"Successfully updated RulePack {domain}:{name}")
        return response

    async def unregister(
        self, domain: str, name: str, version: str | None = None
    ) -> dict[str, Any]:
        """
        Unregister a RulePack.

        Args:
            domain: RulePack domain
            name: RulePack name
            version: Specific version to unregister (default: all versions)

        Returns:
            Unregistration confirmation
        """
        path = f"rulepacks/{domain}/{name}"
        if version:
            path += f"/{version}"

        logger.info(f"Unregistering RulePack {domain}:{name}:{version or 'all'}")

        response = await self._request("DELETE", path)

        logger.info(f"Successfully unregistered RulePack {domain}:{name}")
        return response

    async def discover(
        self, domain: str | None = None, status: RulePackStatus | None = None
    ) -> list[RulePackRegistration]:
        """
        Discover available RulePacks.

        Args:
            domain: Filter by domain (optional)
            status: Filter by status (optional)

        Returns:
            List of available RulePack registrations
        """
        params = {}
        if domain:
            params["domain"] = domain
        if status:
            params["status"] = status.value

        response = await self._request("GET", "rulepacks", params=params)

        return [RulePackRegistration.model_validate(item) for item in response.get("rulepacks", [])]

    async def get(
        self, domain: str, name: str, version: str | None = None
    ) -> RulePackRegistration | None:
        """
        Get specific RulePack registration.

        Args:
            domain: RulePack domain
            name: RulePack name
            version: Specific version (default: latest active)

        Returns:
            RulePack registration or None if not found
        """
        path = f"rulepacks/{domain}/{name}"
        if version:
            path += f"/{version}"

        try:
            response = await self._request("GET", path)
            return RulePackRegistration.model_validate(response)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def health_check(self, domain: str, name: str) -> dict[str, Any]:
        """
        Perform health check on a RulePack and update registry.

        Args:
            domain: RulePack domain
            name: RulePack name

        Returns:
            Health check result
        """
        return await self._request("POST", f"rulepacks/{domain}/{name}/health")

    async def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Registry stats (total rulepacks, by domain, by status, etc.)
        """
        return await self._request("GET", "stats")

    async def auto_register_from_info(
        self, endpoint_url: str, registered_by: str | None = None
    ) -> RulePackRegistration:
        """
        Auto-register a RulePack by fetching its info from endpoint.

        This is a convenience method that calls the RulePack's /info endpoint
        and registers it based on the returned information.

        Args:
            endpoint_url: RulePack endpoint URL
            registered_by: Who is registering this RulePack

        Returns:
            Created registration
        """
        # Fetch RulePack info
        async with httpx.AsyncClient() as client:
            info_response = await client.get(f"{endpoint_url.rstrip('/')}/info")
            info_response.raise_for_status()
            info_data = info_response.json()

        info = RulePackInfo.model_validate(info_data)

        # Create registration
        registration = RulePackRegistration(
            domain=info.domain,
            name=info.name,
            version=info.version,
            endpoint_url=endpoint_url,
            supported_modes=[
                mode.value if hasattr(mode, "value") else mode for mode in info.supported_modes
            ],
            capabilities=info.capabilities,
            metadata=info.metadata,
            registered_by=registered_by,
            health_check_url=f"{endpoint_url.rstrip('/')}/health",
        )

        # Register it
        await self.register(registration)

        logger.info(f"Auto-registered RulePack {info.domain}:{info.name}:{info.version}")
        return registration
