"""Services for FoodInsight API."""

from app.services.sqlite import SQLiteService, get_sqlite_service

# Legacy Firestore (can be removed after migration)
from app.services.firestore import FirestoreClient, get_firestore_client

__all__ = [
    # Primary (SQLite)
    "SQLiteService",
    "get_sqlite_service",
    # Legacy (Firestore)
    "FirestoreClient",
    "get_firestore_client",
]
