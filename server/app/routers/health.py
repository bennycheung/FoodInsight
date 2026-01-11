"""Health check endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends

from app import __version__
from app.config import settings
from app.services.sqlite import SQLiteService, get_sqlite_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
def readiness_check(
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Readiness check - verifies database connectivity."""
    try:
        # Try to read config to verify DB is accessible
        config = service.get_config("device.name")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ready" if db_status == "ok" else "not_ready",
        "database": db_status,
        "device_id": settings.device_id,
    }


@router.get("/info")
def device_info(
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Get device information for client apps."""
    return {
        "device_id": settings.device_id,
        "device_name": service.get_config("device.name") or settings.device_name,
        "location": service.get_config("device.location") or "Unknown",
        "version": __version__,
        "api_docs": "/docs",
    }
