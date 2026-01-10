"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    google_cloud_project: str = ""
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "https://foodinsight.pages.dev",
    ]
    environment: str = "development"


settings = Settings()
