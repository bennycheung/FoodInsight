"""Cloud API client for pushing inventory updates."""

import asyncio
import logging
from typing import Optional

import httpx

from detection.inventory import InventoryDelta

logger = logging.getLogger(__name__)


class CloudAPIClient:
    """Client for communicating with FoodInsight cloud backend.

    Handles pushing inventory delta updates to the FastAPI backend.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        """Initialize the API client.

        Args:
            base_url: Base URL of the cloud API
            api_key: Bearer token for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def push_delta(self, delta: InventoryDelta) -> bool:
        """Push inventory delta to cloud backend.

        Args:
            delta: Inventory delta to push

        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.warning("No API key configured, skipping delta push")
            return False

        client = await self._get_client()
        payload = delta.to_dict()

        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    "/inventory/update",
                    json=payload,
                )
                response.raise_for_status()

                logger.info(
                    f"Delta pushed successfully: {len(delta.events)} events, "
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
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error(f"Failed to push delta after {self.max_retries} attempts")
        return False

    async def health_check(self) -> bool:
        """Check if the cloud backend is reachable.

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

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
