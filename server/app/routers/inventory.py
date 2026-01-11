"""Inventory API endpoints.

Local SQLite-based inventory management for single-device deployment.
"""

import time
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.config import settings
from app.services.sqlite import SQLiteService, get_sqlite_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


# ----- Request/Response Models -----


class InventoryItemUpdate(BaseModel):
    """Single item update from detection pipeline."""

    count: int
    confidence: float = 1.0


class InventoryUpdateRequest(BaseModel):
    """Payload for inventory update from detection pipeline."""

    items: dict[str, InventoryItemUpdate]
    timestamp: datetime | None = None


class InventoryEventCreate(BaseModel):
    """Event to log with inventory update."""

    event_type: str
    item_name: str | None = None
    count_before: int | None = None
    count_after: int | None = None
    confidence: float | None = None
    details: dict | None = None


# ----- Endpoints -----


@router.post("/update")
def update_inventory(
    data: InventoryUpdateRequest,
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Update inventory from detection pipeline.

    Called internally by the detection service after each frame analysis.
    No authentication required for local device communication.
    """
    start_time = time.time()

    # Update each item
    updated_items = []
    for item_name, item_data in data.items.items():
        result = service.update_inventory_item(
            item_name=item_name,
            count=item_data.count,
            confidence=item_data.confidence,
        )
        updated_items.append(result)

    processing_time = time.time() - start_time

    return {
        "status": "ok",
        "device_id": settings.device_id,
        "items_updated": len(updated_items),
        "processing_time_ms": round(processing_time * 1000, 2),
    }


@router.post("/event")
def log_inventory_event(
    event: InventoryEventCreate,
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Log a detection event.

    Called by detection pipeline when inventory changes are detected.
    """
    result = service.log_event(
        event_type=event.event_type,
        item_name=event.item_name,
        count_before=event.count_before,
        count_after=event.count_after,
        confidence=event.confidence,
        details=event.details,
    )
    return {"status": "ok", "event_id": result["id"]}


@router.get("")
def get_inventory(
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Get current inventory state.

    Public endpoint for client app - no authentication required.
    """
    items = service.get_inventory()
    location = service.get_config("device.location") or "Unknown"

    return {
        "device_id": settings.device_id,
        "location": location,
        "items": items,
        "last_updated": max(
            (item["last_updated"] for item in items if item.get("last_updated")),
            default=None,
        ),
    }


@router.get("/item/{item_name}")
def get_inventory_item(
    item_name: str,
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Get a single inventory item by name."""
    item = service.get_inventory_item(item_name)
    if not item:
        return {"error": "Item not found", "item_name": item_name}
    return item


@router.get("/events")
def get_inventory_events(
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
    event_type: Annotated[str | None, Query(description="Filter by event type")] = None,
    item_name: Annotated[str | None, Query(description="Filter by item name")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    """Get recent inventory events.

    Public endpoint - no authentication required.
    """
    events = service.get_events(
        event_type=event_type,
        item_name=item_name,
        limit=limit,
    )
    return {"events": events, "count": len(events)}
