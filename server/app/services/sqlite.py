"""SQLite database service for FoodInsight.

Replaces Firestore with local SQLite storage. All data is stored
on the device with no cloud dependency.
"""

from datetime import datetime, timezone
from typing import Any
import hashlib
import secrets

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.db.models import (
    DEFAULT_CONFIG,
    AdminUser,
    AlertRule,
    AlertType,
    AuditLog,
    Config,
    DetectionEvent,
    EventType,
    InventoryItem,
    UserRole,
)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt.

    For production, consider using bcrypt or argon2.
    This simple implementation works without external dependencies.
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        salt, stored_hash = password_hash.split("$")
        hash_obj = hashlib.sha256((salt + password).encode())
        return hash_obj.hexdigest() == stored_hash
    except ValueError:
        return False


class SQLiteService:
    """Service layer for SQLite database operations.

    Provides a clean interface for all database operations,
    replacing the Firestore client.
    """

    def __init__(self, db: Session):
        """Initialize with a database session.

        Args:
            db: SQLAlchemy session instance
        """
        self.db = db

    # ----- Inventory Operations -----

    def get_inventory(self) -> list[dict[str, Any]]:
        """Get all inventory items.

        Returns:
            List of inventory item dictionaries
        """
        items = self.db.query(InventoryItem).all()
        return [item.to_dict() for item in items]

    def get_inventory_item(self, item_name: str) -> dict[str, Any] | None:
        """Get a single inventory item by name.

        Args:
            item_name: Name of the item

        Returns:
            Item dictionary or None if not found
        """
        item = (
            self.db.query(InventoryItem)
            .filter(InventoryItem.item_name == item_name)
            .first()
        )
        return item.to_dict() if item else None

    def update_inventory_item(
        self,
        item_name: str,
        count: int,
        confidence: float = 1.0,
        max_capacity: int | None = None,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        """Update or create an inventory item.

        Args:
            item_name: Name of the item
            count: Current count
            confidence: Detection confidence
            max_capacity: Maximum capacity for alerts
            display_name: Human-friendly display name

        Returns:
            Updated item dictionary
        """
        item = (
            self.db.query(InventoryItem)
            .filter(InventoryItem.item_name == item_name)
            .first()
        )

        if item:
            item.count = count
            item.confidence = confidence
            if max_capacity is not None:
                item.max_capacity = max_capacity
            if display_name is not None:
                item.display_name = display_name
            item.last_updated = datetime.now(timezone.utc)
        else:
            item = InventoryItem(
                item_name=item_name,
                display_name=display_name or item_name.replace("_", " ").title(),
                count=count,
                confidence=confidence,
                max_capacity=max_capacity,
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(item)
        return item.to_dict()

    def update_inventory_batch(
        self, items: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Update multiple inventory items at once.

        Args:
            items: Dict of item_name -> {count, confidence, ...}

        Returns:
            List of updated item dictionaries
        """
        results = []
        for item_name, data in items.items():
            result = self.update_inventory_item(
                item_name=item_name,
                count=data.get("count", 0),
                confidence=data.get("confidence", 1.0),
                max_capacity=data.get("max_capacity"),
                display_name=data.get("display_name"),
            )
            results.append(result)
        return results

    # ----- Event Operations -----

    def log_event(
        self,
        event_type: EventType | str,
        item_name: str | None = None,
        count_before: int | None = None,
        count_after: int | None = None,
        confidence: float | None = None,
        details: dict | None = None,
    ) -> dict[str, Any]:
        """Log a detection event.

        Args:
            event_type: Type of event
            item_name: Related item name (optional)
            count_before: Count before change (optional)
            count_after: Count after change (optional)
            confidence: Detection confidence (optional)
            details: Additional event details (optional)

        Returns:
            Created event dictionary
        """
        if isinstance(event_type, str):
            event_type = EventType(event_type)

        event = DetectionEvent(
            event_type=event_type,
            item_name=item_name,
            count_before=count_before,
            count_after=count_after,
            confidence=confidence,
            details=details,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event.to_dict()

    def get_events(
        self,
        event_type: EventType | str | None = None,
        item_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get detection events with filters.

        Args:
            event_type: Filter by event type
            item_name: Filter by item name
            start_date: Filter events after this date
            end_date: Filter events before this date
            limit: Maximum events to return
            offset: Offset for pagination

        Returns:
            List of event dictionaries
        """
        query = self.db.query(DetectionEvent)

        if event_type:
            if isinstance(event_type, str):
                event_type = EventType(event_type)
            query = query.filter(DetectionEvent.event_type == event_type)

        if item_name:
            query = query.filter(DetectionEvent.item_name == item_name)

        if start_date:
            query = query.filter(DetectionEvent.timestamp >= start_date)

        if end_date:
            query = query.filter(DetectionEvent.timestamp <= end_date)

        events = (
            query.order_by(DetectionEvent.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [event.to_dict() for event in events]

    # ----- Config Operations -----

    def get_config(self, key: str) -> Any:
        """Get a config value by key.

        Args:
            key: Config key

        Returns:
            Config value or None if not found
        """
        config = self.db.query(Config).filter(Config.key == key).first()
        return config.value if config else None

    def get_all_config(self) -> dict[str, Any]:
        """Get all config as a dictionary.

        Returns:
            Dict of key -> value
        """
        configs = self.db.query(Config).all()
        return {c.key: c.value for c in configs}

    def set_config(
        self,
        key: str,
        value: Any,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Set a config value.

        Args:
            key: Config key
            value: Config value (JSON-serializable)
            description: Optional description

        Returns:
            Updated config dictionary
        """
        config = self.db.query(Config).filter(Config.key == key).first()

        if config:
            config.value = value
            if description is not None:
                config.description = description
            config.updated_at = datetime.now(timezone.utc)
        else:
            config = Config(key=key, value=value, description=description)
            self.db.add(config)

        self.db.commit()
        self.db.refresh(config)
        return config.to_dict()

    def init_default_config(self) -> None:
        """Initialize default configuration values.

        Only sets values that don't already exist.
        """
        for key, data in DEFAULT_CONFIG.items():
            existing = self.db.query(Config).filter(Config.key == key).first()
            if not existing:
                config = Config(
                    key=key,
                    value=data["value"],
                    description=data.get("description"),
                )
                self.db.add(config)
        self.db.commit()

    # ----- User Operations -----

    def get_user(self, username: str) -> dict[str, Any] | None:
        """Get a user by username.

        Args:
            username: Username

        Returns:
            User dictionary or None
        """
        user = (
            self.db.query(AdminUser)
            .filter(AdminUser.username == username)
            .first()
        )
        return user.to_dict() if user else None

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            User dictionary or None
        """
        user = self.db.query(AdminUser).filter(AdminUser.id == user_id).first()
        return user.to_dict() if user else None

    def list_users(self) -> list[dict[str, Any]]:
        """List all users.

        Returns:
            List of user dictionaries
        """
        users = self.db.query(AdminUser).all()
        return [user.to_dict() for user in users]

    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole | str = UserRole.VIEWER,
        display_name: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """Create a new user.

        Args:
            username: Username
            password: Plain text password (will be hashed)
            role: User role
            display_name: Display name
            email: Email address

        Returns:
            Created user dictionary
        """
        if isinstance(role, str):
            role = UserRole(role)

        hashed = hash_password(password)

        user = AdminUser(
            username=username,
            password_hash=hashed,
            role=role,
            display_name=display_name,
            email=email,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user.to_dict()

    def verify_user(self, username: str, password: str) -> dict[str, Any] | None:
        """Verify user credentials.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User dictionary if valid, None otherwise
        """
        user = (
            self.db.query(AdminUser)
            .filter(AdminUser.username == username)
            .filter(AdminUser.is_active == True)  # noqa: E712
            .first()
        )

        if user and verify_password(password, user.password_hash):
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            self.db.commit()
            return user.to_dict()
        return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user.

        Args:
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        user = self.db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False

    def init_default_admin(self) -> None:
        """Create default admin user if no users exist."""
        user_count = self.db.query(AdminUser).count()
        if user_count == 0:
            self.create_user(
                username="admin",
                password="admin",  # Should be changed on first login
                role=UserRole.ADMIN,
                display_name="Administrator",
            )

    # ----- Alert Rule Operations -----

    def get_alert_rules(self) -> list[dict[str, Any]]:
        """Get all alert rules.

        Returns:
            List of alert rule dictionaries
        """
        rules = self.db.query(AlertRule).all()
        return [rule.to_dict() for rule in rules]

    def create_alert_rule(
        self,
        name: str,
        alert_type: AlertType | str,
        item_name: str | None = None,
        threshold: int | None = None,
        is_enabled: bool = True,
    ) -> dict[str, Any]:
        """Create an alert rule.

        Args:
            name: Rule name
            alert_type: Type of alert
            item_name: Item name (optional)
            threshold: Threshold value (optional)
            is_enabled: Whether rule is enabled

        Returns:
            Created rule dictionary
        """
        if isinstance(alert_type, str):
            alert_type = AlertType(alert_type)

        rule = AlertRule(
            name=name,
            alert_type=alert_type,
            item_name=item_name,
            threshold=threshold,
            is_enabled=is_enabled,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule.to_dict()

    # ----- Audit Log Operations -----

    def log_audit(
        self,
        username: str,
        action: str,
        resource: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """Log an audit entry.

        Args:
            username: Username performing action
            action: Action type (e.g., 'config.updated')
            resource: Resource affected
            details: Additional details
            ip_address: Client IP address
            user_id: User ID (optional)

        Returns:
            Created audit log dictionary
        """
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log.to_dict()

    def get_audit_logs(
        self,
        username: str | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get audit logs with filters.

        Args:
            username: Filter by username
            action: Filter by action
            start_date: Filter after this date
            limit: Maximum entries to return
            offset: Offset for pagination

        Returns:
            List of audit log dictionaries
        """
        query = self.db.query(AuditLog)

        if username:
            query = query.filter(AuditLog.username == username)

        if action:
            query = query.filter(AuditLog.action == action)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)

        logs = (
            query.order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [log.to_dict() for log in logs]


# ----- Dependency Injection -----


def get_sqlite_service() -> SQLiteService:
    """FastAPI dependency to get SQLite service.

    Usage:
        @router.get("/inventory")
        async def get_inventory(service: SQLiteService = Depends(get_sqlite_service)):
            return service.get_inventory()
    """
    db = SessionLocal()
    try:
        yield SQLiteService(db)
    finally:
        db.close()
