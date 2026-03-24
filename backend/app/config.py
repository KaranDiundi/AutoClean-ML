"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised config – populated from env vars or .env file."""

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://autoclean:autoclean_secret@localhost:5432/autoclean"
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://autoclean:autoclean_secret@localhost:5432/autoclean"
    )

    # ── Redis / Celery ────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── File storage ──────────────────────────────────────────
    FILE_STORAGE_PATH: str = "/data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 200

    # ── API ───────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    RATE_LIMIT: str = "60/minute"
    API_V1_PREFIX: str = "/api/v1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
