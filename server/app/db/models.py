"""SQLAlchemy ORM models for FoodInsight.

Database schema for local SQLite storage:
- inventory: Current snack counts
- events: Detection event log
- config: Device configuration key-value store
- admin_users: Admin portal users with roles
- alert_rules: Alert configuration
- audit_log: Admin action audit trail
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ----- Enums -----


class EventType(str, PyEnum):
    """Types of detection events."""

    SNACK_TAKEN = "SNACK_TAKEN"
    SNACK_ADDED = "SNACK_ADDED"
    DETECTION_STARTED = "DETECTION_STARTED"
    DETECTION_STOPPED = "DETECTION_STOPPED"
    LOW_STOCK_ALERT = "LOW_STOCK_ALERT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class UserRole(str, PyEnum):
    """Admin user roles with increasing privileges."""

    VIEWER = "viewer"  # Read-only access
    OPERATOR = "operator"  # Can start/stop detection
    ADMIN = "admin"  # Full access including user management


class AlertType(str, PyEnum):
    """Types of alerts that can be configured."""

    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DETECTION_ERROR = "DETECTION_ERROR"
    SYSTEM_OFFLINE = "SYSTEM_OFFLINE"


# ----- ORM Models -----


class InventoryItem(Base):
    """Current inventory state for each snack type.

    Stores the latest count and confidence for each detected item.
    Updated by the detection pipeline after each frame analysis.
    """

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=True)  # Human-friendly name
    count = Column(Integer, default=0, nullable=False)
    max_capacity = Column(Integer, nullable=True)  # For low-stock alerts
    confidence = Column(Float, default=0.0)  # Latest detection confidence
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InventoryItem(name={self.item_name}, count={self.count})>"

    def to_dict(self):
        return {
            "id": self.id,
            "item_name": self.item_name,
            "display_name": self.display_name,
            "count": self.count,
            "max_capacity": self.max_capacity,
            "confidence": self.confidence,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class DetectionEvent(Base):
    """Log of detection events and inventory changes.

    Records every significant event from the detection pipeline,
    including snack count changes, system status, and errors.
    """

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    item_name = Column(String(100), nullable=True, index=True)  # Null for system events
    count_before = Column(Integer, nullable=True)
    count_after = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)  # Additional event metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<DetectionEvent(type={self.event_type}, item={self.item_name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type.value if self.event_type else None,
            "item_name": self.item_name,
            "count_before": self.count_before,
            "count_after": self.count_after,
            "confidence": self.confidence,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class Config(Base):
    """Device configuration key-value store.

    Stores all configurable settings for the device:
    - Detection parameters (threshold, interval, model)
    - Alert thresholds
    - Device metadata (name, location)
    - System settings
    """

    __tablename__ = "config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=True)  # Can store any JSON-serializable value
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Config(key={self.key})>"

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AdminUser(Base):
    """Admin portal users with role-based access.

    Roles:
    - viewer: Read-only dashboard access
    - operator: Can start/stop detection, view logs
    - admin: Full access including user management
    """

    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    display_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to audit logs
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self):
        return f"<AdminUser(username={self.username}, role={self.role})>"

    def to_dict(self, include_sensitive=False):
        data = {
            "id": self.id,
            "username": self.username,
            "role": self.role.value if self.role else None,
            "display_name": self.display_name,
            "email": self.email,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data


class AlertRule(Base):
    """Alert configuration rules.

    Defines when alerts should be triggered:
    - LOW_STOCK: When item count drops below threshold
    - OUT_OF_STOCK: When item count reaches 0
    - DETECTION_ERROR: When detection fails repeatedly
    - SYSTEM_OFFLINE: When device goes offline
    """

    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    item_name = Column(String(100), nullable=True)  # Null for global rules
    threshold = Column(Integer, nullable=True)  # e.g., low stock threshold
    is_enabled = Column(Boolean, default=True)
    notify_email = Column(Boolean, default=False)
    notify_webhook = Column(Boolean, default=False)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AlertRule(name={self.name}, type={self.alert_type})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "item_name": self.item_name,
            "threshold": self.threshold,
            "is_enabled": self.is_enabled,
            "notify_email": self.notify_email,
            "notify_webhook": self.notify_webhook,
            "webhook_url": self.webhook_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    """Audit trail for all admin actions.

    Records every action taken through the admin portal:
    - Configuration changes
    - User management
    - System operations (reboot, shutdown)
    - Detection control (start, stop)
    """

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
    username = Column(String(50), nullable=False)  # Denormalized for easy lookup
    action = Column(String(100), nullable=False, index=True)  # e.g., 'config.updated'
    resource = Column(String(100), nullable=True)  # e.g., 'detection_threshold'
    details = Column(JSON, nullable=True)  # e.g., {old: 5, new: 3}
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship to user
    user = relationship("AdminUser", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(user={self.username}, action={self.action})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# ----- Default Configuration Values -----

DEFAULT_CONFIG = {
    # Device metadata
    "device.name": {"value": "FoodInsight Device", "description": "Device display name"},
    "device.location": {"value": "Break Room", "description": "Device location"},
    # Detection settings
    "detection.model": {"value": "yolo11s-snacks.hef", "description": "Detection model file"},
    "detection.confidence_threshold": {"value": 0.5, "description": "Minimum detection confidence"},
    "detection.interval_ms": {"value": 100, "description": "Detection interval in milliseconds"},
    "detection.motion_enabled": {"value": True, "description": "Enable motion-triggered detection"},
    "detection.motion_threshold": {"value": 0.02, "description": "Motion detection sensitivity"},
    # Alert settings
    "alerts.low_stock_threshold": {"value": 3, "description": "Default low stock alert threshold"},
    "alerts.email_enabled": {"value": False, "description": "Enable email notifications"},
    "alerts.email_recipients": {"value": [], "description": "Email recipients for alerts"},
    # Privacy settings
    "privacy.mode": {"value": "inventory_only", "description": "Privacy mode (none, inventory_only, hands, full)"},
    "privacy.blur_strength": {"value": 51, "description": "Blur kernel size for privacy"},
    # System settings
    "system.timezone": {"value": "UTC", "description": "Device timezone"},
    "system.log_retention_days": {"value": 90, "description": "Days to retain logs"},
}
