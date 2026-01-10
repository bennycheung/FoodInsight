"""Bearer token authentication."""

import hashlib
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.firestore import FirestoreClient, get_firestore_client

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    """Hash a token for secure storage comparison.

    Args:
        token: Raw API token

    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


async def verify_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    company: Annotated[str, Query(description="Company identifier")],
    db: Annotated[FirestoreClient, Depends(get_firestore_client)],
) -> dict:
    """Verify Bearer token against company's stored API keys.

    Args:
        credentials: HTTP Bearer credentials
        company: Company identifier from query param
        db: Firestore client

    Returns:
        Dict with company, machine_id, and machine_name

    Raises:
        HTTPException: If token is invalid or not found
    """
    token = credentials.credentials
    token_hash = hash_token(token)

    # Get all machines for company and check token
    machines_ref = (
        db.db.collection("companies").document(company).collection("machines")
    )

    try:
        machines = machines_ref.stream()
        async for machine in machines:
            machine_data = machine.to_dict()
            stored_hash = machine_data.get("config", {}).get("api_key_hash")
            if stored_hash and stored_hash == token_hash:
                return {
                    "company": company,
                    "machine_id": machine.id,
                    "machine_name": machine_data.get("name"),
                }
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )


async def optional_auth(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_security)
    ],
    company: Annotated[str | None, Query(description="Company identifier")] = None,
    db: Annotated[FirestoreClient, Depends(get_firestore_client)] = None,
) -> dict | None:
    """Optional authentication - returns None if no token provided.

    Args:
        credentials: Optional HTTP Bearer credentials
        company: Optional company identifier
        db: Firestore client

    Returns:
        Auth dict or None if no credentials
    """
    if credentials is None or company is None:
        return None
    return await verify_token(credentials, company, db)
