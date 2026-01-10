"""Health check endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter

from app import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes/Cloud Run.

    Add dependency checks here (Firestore, etc.) when implemented.
    """
    return {"status": "ready"}
