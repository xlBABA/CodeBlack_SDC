"""Typed environment configuration for the FuturePath AI backend."""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "FuturePath AI Backend"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # SQLite now; same variable swaps to a Postgres DSN later without code changes.
    DATABASE_URL: str = "sqlite:///./futurepath.db"

    CORS_ORIGINS: str = "http://localhost:5173"

    # Fixture adapters stand in until real providers (Hussain/Jawad) are integrated.
    ENABLE_FIXTURES: bool = True

    # Optional provider credentials — absence must never prevent the app from starting.
    LLM_PROVIDER: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    RUNPOD_API_KEY: Optional[str] = None
    RUNPOD_ENDPOINT_ID: Optional[str] = None
    TREND_SOURCE_API_KEY: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
