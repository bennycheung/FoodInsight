#!/usr/bin/env python3
"""Generate API token for edge device registration."""

import hashlib
import secrets
import sys


def generate_api_key(prefix: str = "sk") -> tuple[str, str]:
    """Generate API key and its hash.

    Args:
        prefix: Token prefix (e.g., "sk_acme" for company acme)

    Returns:
        Tuple of (raw_token, token_hash)
    """
    token = f"{prefix}_{secrets.token_urlsafe(24)}"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else "sk"

    token, token_hash = generate_api_key(prefix)

    print(f"API Token (give to edge device): {token}")
    print(f"Token Hash (store in Firestore):  {token_hash}")
    print()
    print("Store the hash in Firestore at:")
    print("  companies/{company}/machines/{machine_id}")
    print("  → config.api_key_hash = <token_hash>")
