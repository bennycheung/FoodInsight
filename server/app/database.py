"""SQLite database configuration using SQLAlchemy."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Database file path - relative to project root
DB_PATH = Path(settings.database_path)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# SQLite connection URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for FastAPI
    echo=settings.database_echo,  # Log SQL queries in dev
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """FastAPI dependency to get database session.

    Usage:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables.

    Call this on application startup to create tables if they don't exist.
    """
    from app.db import models  # noqa: F401 - Import to register models

    Base.metadata.create_all(bind=engine)
