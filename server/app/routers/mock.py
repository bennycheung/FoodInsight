"""Mock endpoints for local development without Firestore."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Header

from app.models.inventory import InventoryUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["inventory-mock"])

# Allowed items filter (empty list = accept all items)
# These match the default COCO food classes from edge device
ALLOWED_ITEMS: list[str] = [
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
    "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
    "hot dog", "pizza", "donut", "cake",
]

# In-memory storage for mock data (starts empty, persists during server lifetime)
_mock_inventories: dict[str, dict] = {}

# Event log for debugging
_mock_events: list[dict] = []


@router.post("/update")
async def update_mock_inventory(
    data: InventoryUpdate,
    authorization: str = Header(default="Bearer mock-token"),
):
    """Accept inventory updates from edge device (mock - no auth validation).

    This endpoint mimics the production /inventory/update endpoint
    but stores data in memory instead of Firestore.
    Items are filtered against ALLOWED_ITEMS if configured.
    """
    machine_id = data.machine_id
    now = datetime.now(timezone.utc).isoformat()

    # Initialize machine if not exists
    if machine_id not in _mock_inventories:
        _mock_inventories[machine_id] = {
            "location": "Unknown",
            "items": {},
            "last_updated": now,
        }

    # Update items (filter to allowed items if configured)
    items_updated = 0
    for item_name, item_data in data.items.items():
        if ALLOWED_ITEMS and item_name not in ALLOWED_ITEMS:
            logger.debug(f"Skipping non-allowed item: {item_name}")
            continue
        _mock_inventories[machine_id]["items"][item_name] = {
            "count": item_data.count,
            "confidence": item_data.confidence,
        }
        items_updated += 1

    _mock_inventories[machine_id]["last_updated"] = now

    # Log events (filter to allowed items if configured)
    events_logged = 0
    for event in data.events:
        if ALLOWED_ITEMS and event.item not in ALLOWED_ITEMS:
            logger.debug(f"Skipping event for non-allowed item: {event.item}")
            continue
        event_record = {
            "machine_id": machine_id,
            "timestamp": now,
            **event.model_dump(),
        }
        _mock_events.append(event_record)
        events_logged += 1
        logger.info(f"Mock event: {event.type} - {event.item}")

    logger.info(
        f"Mock inventory updated: {machine_id} - {items_updated} items, "
        f"{events_logged} events"
    )

    return {
        "status": "ok",
        "machine_id": machine_id,
        "items_updated": items_updated,
        "events_logged": events_logged,
        "processing_time_ms": 1.0,
    }


@router.get("/{machine_id}")
async def get_mock_inventory(machine_id: str, company: str = "demo"):
    """Return mock inventory for local testing."""
    if machine_id in _mock_inventories:
        inventory = _mock_inventories[machine_id]
        return {
            "machine_id": machine_id,
            "location": inventory["location"],
            "items": inventory["items"],
            "last_updated": inventory["last_updated"],
        }

    # Return default empty inventory for unknown machines
    return {
        "machine_id": machine_id,
        "location": "Unknown",
        "items": {},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{machine_id}/events")
async def get_mock_events(machine_id: str, company: str = "demo", limit: int = 50):
    """Return recent events for a machine (mock)."""
    machine_events = [e for e in _mock_events if e["machine_id"] == machine_id]
    return {"events": machine_events[-limit:]}


@router.delete("/{machine_id}")
async def reset_mock_inventory(machine_id: str):
    """Reset inventory for a machine (mock - for testing)."""
    if machine_id in _mock_inventories:
        del _mock_inventories[machine_id]

    # Clear events for this machine
    global _mock_events
    _mock_events = [e for e in _mock_events if e["machine_id"] != machine_id]

    logger.info(f"Mock inventory reset: {machine_id}")
    return {"status": "ok", "machine_id": machine_id, "message": "Inventory reset"}


@router.delete("/")
async def reset_all_mock_inventories():
    """Reset all inventories (mock - for testing)."""
    global _mock_events
    _mock_inventories.clear()
    _mock_events = []

    logger.info("All mock inventories reset")
    return {"status": "ok", "message": "All inventories reset"}


@router.get("/")
async def list_mock_inventories():
    """List all machines with inventories (mock)."""
    return {
        "machines": list(_mock_inventories.keys()),
        "allowed_items": ALLOWED_ITEMS,
    }
