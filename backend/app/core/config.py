#!/usr/bin/env python3
"""Configuration management for subscout backend."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "subscout"
    VERSION: str = "0.1.0"

    HOME_DIR: Path = Path.home() / ".subscout"
    UPLOAD_DIR: Path = HOME_DIR / "uploads"
    CACHE_DIR: Path = HOME_DIR / "cache"

    DATABASE_URL: str = f"sqlite+aiosqlite:///{HOME_DIR}/subscout.db"

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend port
        "http://localhost:8000",  # Production (same origin)
    ]

    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set[str] = {".srt", ".ass"}

    SESSION_EXPIRY_HOURS: int = 24

    DEFAULT_USER: str = "default"

    class Config:
        env_file = ".env"
        case_sensitive = True


def init_directories():
    """Initialize required directories."""
    settings = Settings()
    settings.HOME_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
