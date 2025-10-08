"""
CORTX Platform Client
"""
import httpx
from typing import Optional
from cortx_backend.common.models import ComplianceEvent

class CortexClient:
    def __init__(self, base_url: str, client: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip('/')
        self.client = client or httpx.Client(timeout=10)

    def log_compliance_event(self, event: ComplianceEvent):
        """Logs a compliance event to the CORTX compliance service."""
        if not self.base_url:
            return

        # Ensure the event is signed with a hash
        event.sign()

        try:
            response = self.client.post(
                f"{self.base_url}/v1/compliance/log",
                content=event.model_dump_json(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # In a real app, you'd have structured logging here
            print(f"Error logging compliance event: {e}")
        except httpx.RequestError as e:
            print(f"Request error logging compliance event: {e}")
