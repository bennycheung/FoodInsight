"""Local API client for pushing inventory updates.

Communicates with the local FastAPI backend for inventory and event tracking.
No authentication required for local device-to-server communication.
"""

import asyncio
import logging
from typing import Optional

import httpx

from detection.inventory import InventoryDelta, InventoryEvent

logger = logging.getLogger(__name__)


class LocalAPIClient:
    """Client for communicating with local FoodInsight FastAPI backend.

    Handles pushing inventory updates and events to the local SQLite-backed server.
    No authentication required for inventory endpoints (local trust model).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 5.0,
        max_retries: int = 3,
    ):
        """Initialize the local API client.

        Args:
            base_url: Base URL of the local FastAPI server
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def push_delta(self, delta: InventoryDelta) -> bool:
        """Push inventory delta to local backend.

        Args:
            delta: Inventory delta to push

        Returns:
            True if successful, False otherwise
        """
        client = await self._get_client()
        payload = delta.to_dict()

        for attempt in range(self.max_retries):
            try:
                # Push inventory update
                response = await client.post(
                    "/inventory/update",
                    json=payload,
                )
                response.raise_for_status()

                # Push individual events
                for event in delta.events:
                    await self._push_event(client, event)

                logger.info(
                    f"Delta pushed: {len(delta.events)} events, "
                    f"{len(delta.inventory)} items"
                )
                return True

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error pushing delta (attempt {attempt + 1}): "
                    f"{e.response.status_code} - {e.response.text}"
                )
            except httpx.RequestError as e:
                logger.error(
                    f"Request error pushing delta (attempt {attempt + 1}): {e}"
                )

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))

        logger.error(f"Failed to push delta after {self.max_retries} attempts")
        return False

    async def _push_event(self, client: httpx.AsyncClient, event: InventoryEvent) -> bool:
        """Push a single inventory event."""
        try:
            payload = {
                "event_type": event.type.value,
                "item_name": event.item,
                "count_before": event.count_before,
                "count_after": event.count_after,
                "confidence": 1.0,
                "details": {"track_id": event.track_id},
            }
            response = await client.post("/inventory/event", json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Failed to push event: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if the local backend is reachable.

        Returns:
            True if healthy, False otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def get_inventory(self) -> Optional[dict]:
        """Get current inventory from backend."""
        try:
            client = await self._get_client()
            response = await client.get("/inventory")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Failed to get inventory: {e}")
            return None

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


# Backwards compatibility alias
CloudAPIClient = LocalAPIClient
