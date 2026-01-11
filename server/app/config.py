"""Application configuration using Pydantic settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Environment
    environment: str = "development"

    # Database (SQLite)
    database_path: str = str(Path(__file__).parent.parent / "data" / "foodinsight.db")
    database_echo: bool = False  # Log SQL queries (set True for debugging)

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8000",
    ]

    # Security
    secret_key: str = "change-me-in-production"  # For session/token signing
    access_token_expire_minutes: int = 30

    # Device identification
    device_id: str = "foodinsight-001"
    device_name: str = "FoodInsight Device"

    # Legacy (can be removed once Firestore migration complete)
    google_cloud_project: str = ""


settings = Settings()
