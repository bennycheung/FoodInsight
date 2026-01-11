"""Admin API endpoints.

Protected endpoints for device administration via the admin portal.
Requires HTTP Basic authentication with role-based access control.
"""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from app.config import settings
from app.db.models import UserRole
from app.services.sqlite import SQLiteService, get_sqlite_service

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()


# ----- Authentication -----


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
) -> dict:
    """Authenticate user via HTTP Basic auth.

    Returns user dict if valid, raises 401 otherwise.
    """
    user = service.verify_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control."""

    def check_role(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return user

    return check_role


# Role shortcuts
require_viewer = require_role("viewer", "operator", "admin")
require_operator = require_role("operator", "admin")
require_admin = require_role("admin")


# ----- Request/Response Models -----


class ConfigUpdate(BaseModel):
    """Configuration update request."""

    key: str
    value: str | int | float | bool | list | dict
    description: str | None = None


class UserCreate(BaseModel):
    """User creation request."""

    username: str
    password: str
    role: str = "viewer"
    display_name: str | None = None
    email: str | None = None


class AlertRuleCreate(BaseModel):
    """Alert rule creation request."""

    name: str
    alert_type: str
    item_name: str | None = None
    threshold: int | None = None
    is_enabled: bool = True


# ----- Device Status Endpoints -----


@router.get("/status")
def get_device_status(
    user: Annotated[dict, Depends(require_viewer)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Get current device status."""
    import os
    import platform

    # Get system info
    try:
        load_avg = os.getloadavg()
    except (OSError, AttributeError):
        load_avg = (0, 0, 0)

    return {
        "device_id": settings.device_id,
        "device_name": service.get_config("device.name") or settings.device_name,
        "location": service.get_config("device.location") or "Unknown",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "load_average": load_avg,
        "environment": settings.environment,
    }


@router.get("/config")
def get_config(
    user: Annotated[dict, Depends(require_viewer)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Get all device configuration."""
    return service.get_all_config()


@router.put("/config")
def update_config(
    data: ConfigUpdate,
    request: Request,
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Update a configuration value."""
    old_value = service.get_config(data.key)

    result = service.set_config(
        key=data.key,
        value=data.value,
        description=data.description,
    )

    # Audit log
    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="config.updated",
        resource=data.key,
        details={"old": old_value, "new": data.value},
        ip_address=request.client.host if request.client else None,
    )

    return result


# ----- Detection Control Endpoints -----


@router.get("/detection/status")
def get_detection_status(
    user: Annotated[dict, Depends(require_viewer)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Get detection pipeline status."""
    # This would integrate with the actual detection service
    # For now, return config-based status
    return {
        "status": "running",  # TODO: Get actual status from detection service
        "model": service.get_config("detection.model"),
        "confidence_threshold": service.get_config("detection.confidence_threshold"),
        "interval_ms": service.get_config("detection.interval_ms"),
        "motion_enabled": service.get_config("detection.motion_enabled"),
    }


@router.post("/detection/start")
def start_detection(
    request: Request,
    user: Annotated[dict, Depends(require_operator)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Start the detection pipeline."""
    # TODO: Integrate with actual detection service
    service.log_event("DETECTION_STARTED", details={"started_by": user["username"]})
    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="detection.started",
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "ok", "message": "Detection started"}


@router.post("/detection/stop")
def stop_detection(
    request: Request,
    user: Annotated[dict, Depends(require_operator)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Stop the detection pipeline."""
    # TODO: Integrate with actual detection service
    service.log_event("DETECTION_STOPPED", details={"stopped_by": user["username"]})
    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="detection.stopped",
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "ok", "message": "Detection stopped"}


# ----- User Management Endpoints -----


@router.get("/users")
def list_users(
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """List all admin users."""
    return {"users": service.list_users()}


@router.post("/users")
def create_user(
    data: UserCreate,
    request: Request,
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Create a new admin user."""
    # Check if username exists
    existing = service.get_user(data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Validate role
    try:
        UserRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {[r.value for r in UserRole]}",
        )

    new_user = service.create_user(
        username=data.username,
        password=data.password,
        role=data.role,
        display_name=data.display_name,
        email=data.email,
    )

    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="user.created",
        resource=data.username,
        details={"role": data.role},
        ip_address=request.client.host if request.client else None,
    )

    return new_user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Delete an admin user."""
    # Prevent self-deletion
    if user_id == user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    target_user = service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    service.delete_user(user_id)

    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="user.deleted",
        resource=target_user["username"],
        ip_address=request.client.host if request.client else None,
    )

    return {"status": "ok", "message": "User deleted"}


# ----- Alert Rules Endpoints -----


@router.get("/alerts")
def list_alert_rules(
    user: Annotated[dict, Depends(require_viewer)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """List all alert rules."""
    return {"rules": service.get_alert_rules()}


@router.post("/alerts")
def create_alert_rule(
    data: AlertRuleCreate,
    request: Request,
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Create a new alert rule."""
    rule = service.create_alert_rule(
        name=data.name,
        alert_type=data.alert_type,
        item_name=data.item_name,
        threshold=data.threshold,
        is_enabled=data.is_enabled,
    )

    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="alert.created",
        resource=data.name,
        details={"type": data.alert_type, "threshold": data.threshold},
        ip_address=request.client.host if request.client else None,
    )

    return rule


# ----- Events & Audit Endpoints -----


@router.get("/events")
def get_events(
    user: Annotated[dict, Depends(require_viewer)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
    event_type: str | None = None,
    item_name: str | None = None,
    limit: int = 100,
):
    """Get detection events with filters."""
    events = service.get_events(
        event_type=event_type,
        item_name=item_name,
        limit=limit,
    )
    return {"events": events, "count": len(events)}


@router.get("/audit")
def get_audit_logs(
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
    username: str | None = None,
    action: str | None = None,
    limit: int = 100,
):
    """Get admin audit logs."""
    logs = service.get_audit_logs(
        username=username,
        action=action,
        limit=limit,
    )
    return {"logs": logs, "count": len(logs)}


# ----- System Operations -----


@router.post("/system/reboot")
def reboot_device(
    request: Request,
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Schedule device reboot."""
    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="system.reboot_requested",
        ip_address=request.client.host if request.client else None,
    )
    # TODO: Actually schedule reboot via systemd or similar
    return {"status": "ok", "message": "Reboot scheduled"}


@router.post("/system/shutdown")
def shutdown_device(
    request: Request,
    user: Annotated[dict, Depends(require_admin)],
    service: Annotated[SQLiteService, Depends(get_sqlite_service)],
):
    """Schedule device shutdown."""
    service.log_audit(
        username=user["username"],
        user_id=user["id"],
        action="system.shutdown_requested",
        ip_address=request.client.host if request.client else None,
    )
    # TODO: Actually schedule shutdown via systemd or similar
    return {"status": "ok", "message": "Shutdown scheduled"}


@router.get("/system/logs")
def get_system_logs(
    user: Annotated[dict, Depends(require_admin)],
    lines: int = 100,
):
    """Get recent system logs."""
    # TODO: Read from actual log files
    return {
        "logs": [],
        "message": "System log integration pending",
    }
