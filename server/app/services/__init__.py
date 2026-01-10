"""Services for FoodInsight API."""

from app.services.firestore import FirestoreClient, get_firestore_client

__all__ = ["FirestoreClient", "get_firestore_client"]
