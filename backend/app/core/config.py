"""Typed environment configuration for the FuturePath AI backend."""
from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr, field_validator
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

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _reject_wildcard_origin(cls, value: str) -> str:
        # main.py always sets allow_credentials=True; a wildcard origin
        # combined with credentials is both a browser-rejected combination
        # and a real security risk, so invalid config fails loudly at
        # startup rather than silently degrading CORS protection.
        parts = [part.strip() for part in value.split(",") if part.strip()]
        if "*" in parts:
            raise ValueError(
                "CORS_ORIGINS must not include '*' — this backend always "
                "sends allow_credentials=True; list explicit trusted "
                "origins instead."
            )
        return value

    # Fixture adapters stand in until real providers (Hussain/Jawad) are
    # integrated. False signals "I expect real inference" — Milestone 6A
    # wires this into get_matching_provider() so that case fails loudly
    # (PROVIDER_UNAVAILABLE) rather than silently serving fixture output,
    # since no real MatchingProvider implementation exists yet.
    ENABLE_FIXTURES: bool = True

    # Reserved for a future real provider's own HTTP client to apply.
    # Nothing in this codebase enforces this today — no real provider
    # makes a blocking network call yet, so there's nothing to time out.
    PROVIDER_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0)

    # Optional provider credentials — absence must never prevent the app
    # from starting. SecretStr keeps them out of accidental repr()/str()
    # logging (e.g. `logger.info(settings)`) — they render as "**********"
    # instead of the real value. Never log/return .get_secret_value().
    LLM_PROVIDER: Optional[str] = None
    LLM_API_KEY: Optional[SecretStr] = None
    RUNPOD_API_KEY: Optional[SecretStr] = None
    RUNPOD_ENDPOINT_ID: Optional[str] = None  # identifier, not a secret
    TREND_SOURCE_API_KEY: Optional[SecretStr] = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
