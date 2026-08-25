# config.py
# ─────────────────────────────────────────────────────────────────────────────
# Central configuration hub. All environment variables are read ONCE here.
# Every other module imports from config — never from os.environ directly.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Skellix API"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "Career Skill Assessment Platform — Backend API"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────────────────
    # SQLite file path. For PostgreSQL later, just swap this value.
    # Example (future): "postgresql://user:pass@localhost:5432/skellix"
    DATABASE_URL: str = "sqlite:///./skellix.db"

    # ── AI Service ───────────────────────────────────────────────────────────
    # OpenAI API key — loaded from .env file, never hardcoded.
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT_SECONDS: int = 10       # Max wait before giving up on AI
    OPENAI_MAX_RETRIES: int = 1            # Retry once on failure, then fallback

    # ── Assessment Logic ─────────────────────────────────────────────────────
    # Minimum score (%) to consider a skill "passed" — used by gap detection
    SKILL_PASS_THRESHOLD: float = 60.0
    # Number of questions to serve per skill during assessment
    QUESTIONS_PER_SKILL: int = 5

    # ── Security ─────────────────────────────────────────────────────────────
    # Secret key for session UUID signing (not critical for MVP but good habit)
    SECRET_KEY: str = "skellix-dev-secret-change-in-production"

    class Config:
        # Reads from a .env file automatically if present
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allows extra fields in .env without crashing
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Using lru_cache ensures the .env file is read only ONCE per process,
    not on every request. Import and call this wherever settings are needed.

    Usage:
        from config import get_settings
        settings = get_settings()
        print(settings.APP_NAME)
    """
    return Settings()
