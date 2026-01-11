#!/usr/bin/env python3
"""Initialize the FoodInsight SQLite database.

Creates all tables and populates with default configuration.

Usage:
    cd server
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, SessionLocal
from app.services.sqlite import SQLiteService


def main():
    """Initialize database with tables and default data."""
    print("Initializing FoodInsight database...")

    # Create all tables
    print("  Creating tables...")
    init_db()

    # Initialize default data
    db = SessionLocal()
    try:
        service = SQLiteService(db)

        print("  Loading default configuration...")
        service.init_default_config()

        print("  Creating default admin user...")
        service.init_default_admin()

        print("\nDatabase initialized successfully!")
        print("\nDefault admin credentials:")
        print("  Username: admin")
        print("  Password: admin")
        print("\n⚠️  Please change the admin password after first login!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
