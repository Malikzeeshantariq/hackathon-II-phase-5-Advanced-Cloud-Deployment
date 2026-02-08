"""T008: Environment configuration module.

Spec Reference: plan.md - Environment Variables section
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

# Project root .env file (one level up from backend/)
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        BETTER_AUTH_SECRET: Shared secret for JWT verification
        DATABASE_URL: Neon PostgreSQL connection string
        CORS_ORIGINS: Comma-separated list of allowed origins
    """

    # Shared Secret (not used - backend verifies via JWKS public keys)
    BETTER_AUTH_SECRET: str = ""

    # Database
    DATABASE_URL: str

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Better Auth JWKS endpoint URL
    BETTER_AUTH_URL: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore frontend env vars like NEXT_PUBLIC_*


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
