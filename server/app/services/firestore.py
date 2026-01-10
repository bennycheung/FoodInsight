"""Firestore database service."""

from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore

from app.config import settings
from app.models.inventory import InventoryItem, MachineConfig


class FirestoreClient:
    """Async Firestore client for FoodInsight data.

    Data is organized by company for multi-tenant support:
    companies/{company}/machines/{machine_id}
    companies/{company}/inventory/{machine_id}
    companies/{company}/events/{event_id}
    """

    def __init__(self, project_id: str | None = None):
        """Initialize Firestore client.

        Args:
            project_id: GCP project ID. If None, uses default from environment.
        """
        self.db = firestore.AsyncClient(
            project=project_id or settings.google_cloud_project or None
        )

    # Machine operations

    async def get_machine(self, company: str, machine_id: str) -> dict[str, Any] | None:
        """Get machine document by ID.

        Args:
            company: Company identifier
            machine_id: Machine identifier

        Returns:
            Machine document data or None if not found
        """
        doc = (
            await self.db.collection("companies")
            .document(company)
            .collection("machines")
            .document(machine_id)
            .get()
        )
        return doc.to_dict() if doc.exists else None

    async def create_machine(
        self,
        company: str,
        machine_id: str,
        config: MachineConfig,
    ) -> None:
        """Create a new machine document.

        Args:
            company: Company identifier
            machine_id: Machine identifier
            config: Machine configuration
        """
        await (
            self.db.collection("companies")
            .document(company)
            .collection("machines")
            .document(machine_id)
            .set(
                {
                    "name": config.name,
                    "location": config.location,
                    "status": "offline",
                    "last_seen": None,
                    "config": {"api_key_hash": config.api_key_hash},
                }
            )
        )

    async def update_machine_status(
        self,
        company: str,
        machine_id: str,
        status: str = "online",
    ) -> None:
        """Update machine status and last_seen timestamp.

        Args:
            company: Company identifier
            machine_id: Machine identifier
            status: New status (online/offline)
        """
        await (
            self.db.collection("companies")
            .document(company)
            .collection("machines")
            .document(machine_id)
            .update(
                {
                    "status": status,
                    "last_seen": datetime.now(timezone.utc),
                }
            )
        )

    # Inventory operations

    async def get_inventory(
        self, company: str, machine_id: str
    ) -> dict[str, Any] | None:
        """Get inventory document for a machine.

        Args:
            company: Company identifier
            machine_id: Machine identifier

        Returns:
            Inventory document data or None if not found
        """
        doc = (
            await self.db.collection("companies")
            .document(company)
            .collection("inventory")
            .document(machine_id)
            .get()
        )
        return doc.to_dict() if doc.exists else None

    async def update_inventory(
        self,
        company: str,
        machine_id: str,
        items: dict[str, InventoryItem],
    ) -> None:
        """Update inventory for a machine.

        Args:
            company: Company identifier
            machine_id: Machine identifier
            items: Dictionary of item name to InventoryItem
        """
        now = datetime.now(timezone.utc)

        # Build inventory data
        inventory_data = {
            "items": {
                name: {
                    "count": item.count,
                    "confidence": item.confidence,
                    "last_updated": now,
                }
                for name, item in items.items()
            },
            "last_updated": now,
        }

        # Update inventory document
        await (
            self.db.collection("companies")
            .document(company)
            .collection("inventory")
            .document(machine_id)
            .set(inventory_data, merge=True)
        )

        # Update machine last_seen
        await self.update_machine_status(company, machine_id, "online")

    # Event operations

    async def log_event(
        self,
        company: str,
        machine_id: str,
        event: dict[str, Any],
    ) -> str:
        """Log an inventory event.

        Args:
            company: Company identifier
            machine_id: Machine identifier
            event: Event data dictionary

        Returns:
            Created event document ID
        """
        events_ref = (
            self.db.collection("companies").document(company).collection("events")
        )

        doc_ref = await events_ref.add(
            {
                **event,
                "machine_id": machine_id,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        return doc_ref[1].id

    async def get_events(
        self,
        company: str,
        machine_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get recent events for a company.

        Args:
            company: Company identifier
            machine_id: Optional filter by machine
            limit: Maximum events to return

        Returns:
            List of event documents
        """
        query = (
            self.db.collection("companies")
            .document(company)
            .collection("events")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )

        if machine_id:
            query = query.where("machine_id", "==", machine_id)

        docs = await query.get()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]


# Dependency injection helper
_firestore_client: FirestoreClient | None = None


def get_firestore_client() -> FirestoreClient:
    """Get or create Firestore client singleton.

    Returns:
        FirestoreClient instance
    """
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = FirestoreClient()
    return _firestore_client
