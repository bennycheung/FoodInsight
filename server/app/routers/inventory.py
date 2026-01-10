"""Inventory API endpoints."""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.token import verify_token
from app.models.inventory import InventoryResponse, InventoryUpdate
from app.services.firestore import FirestoreClient, get_firestore_client

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/update")
async def update_inventory(
    data: InventoryUpdate,
    auth: Annotated[dict, Depends(verify_token)],
    db: Annotated[FirestoreClient, Depends(get_firestore_client)],
):
    """Update inventory from edge device.

    Requires Bearer token authentication.
    Accepts delta updates with current counts and events.
    """
    start_time = time.time()

    company = auth["company"]
    machine_id = auth["machine_id"]

    # Validate machine_id matches token
    if data.machine_id != machine_id:
        raise HTTPException(
            status_code=403,
            detail="Machine ID doesn't match authenticated device",
        )

    # Update inventory
    await db.update_inventory(company, machine_id, data.items)

    # Log events
    event_ids = []
    for event in data.events:
        event_id = await db.log_event(company, machine_id, event.model_dump())
        event_ids.append(event_id)

    processing_time = time.time() - start_time

    return {
        "status": "ok",
        "machine_id": machine_id,
        "items_updated": len(data.items),
        "events_logged": len(event_ids),
        "processing_time_ms": round(processing_time * 1000, 2),
    }


@router.get("/{machine_id}", response_model=InventoryResponse)
async def get_inventory(
    machine_id: str,
    company: Annotated[str, Query(description="Company identifier")],
    db: Annotated[FirestoreClient, Depends(get_firestore_client)],
):
    """Get current inventory for a machine.

    Public endpoint - no authentication required.
    """
    inventory = await db.get_inventory(company, machine_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Get machine info for location
    machine = await db.get_machine(company, machine_id)

    # Convert Firestore items to InventoryItem format
    items = {}
    for name, item_data in inventory.get("items", {}).items():
        items[name] = {
            "count": item_data.get("count", 0),
            "confidence": item_data.get("confidence", 1.0),
        }

    return InventoryResponse(
        machine_id=machine_id,
        location=machine.get("location", "Unknown") if machine else "Unknown",
        items=items,
        last_updated=inventory.get("last_updated"),
    )


@router.get("/{machine_id}/events")
async def get_inventory_events(
    machine_id: str,
    company: Annotated[str, Query(description="Company identifier")],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Annotated[FirestoreClient, Depends(get_firestore_client)] = None,
):
    """Get recent events for a machine.

    Public endpoint - no authentication required.
    """
    events = await db.get_events(company, machine_id, limit)
    return {"events": events}
