"""Typed environment configuration for the FuturePath AI backend."""
from functools import lru_cache
from typing import Literal, Optional

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

    # Which RoleCatalogProvider get_role_catalog() selects — independent of
    # ENABLE_FIXTURES (that gates the *scoring* provider; this gates the
    # *role/skill data* provider). "cached" selects Jawad's validated
    # O*NET-derived catalog (app/services/role_catalog_cached.py); matching
    # itself still runs through FixtureMatchingProvider either way until
    # Hussain's provider is integrated. Any value other than the two
    # listed below fails Settings() construction immediately (pydantic
    # Literal validation), never silently falls back to "fixture".
    CATALOG_MODE: Literal["fixture", "cached"] = "fixture"

    # Which MatchingProvider get_matching_provider() selects. "hussain"
    # selects the vendored, offline HussainMatchingProvider
    # (app/services/hussain_matching) — semantic similarity/RunPod is
    # never activated by this setting alone (see careers.py's explicit
    # no-similarity wiring). Independent of CATALOG_MODE (role/skill data)
    # and ENABLE_FIXTURES (whether any fixture-sourced data may be served
    # at all — see get_matching_provider()'s fail-closed interaction with
    # this setting). Any other value fails Settings() construction
    # immediately, never silently falls back to "fixture".
    MATCHING_MODE: Literal["fixture", "hussain"] = "fixture"

    # Reserved for a future real provider's own HTTP client to apply.
    # Nothing in this codebase enforces this today — no real provider
    # makes a blocking network call yet, so there's nothing to time out.
    PROVIDER_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0)

    # Optional provider credentials — absence must never prevent the app
    # from starting. SecretStr keeps them out of accidental repr()/str()
    # logging (e.g. `logger.info(settings)`) — they render as "**********"
    # instead of the real value. Never log/return .get_secret_value().
    # CV extraction and semantic embeddings are separate providers. The
    # default preserves the existing RunPod extraction path; OpenRouter
    # requires its own explicit key, base URL, and model.
    LLM_PROVIDER: Literal["runpod", "openrouter"] = "runpod"
    LLM_API_KEY: Optional[SecretStr] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    LLM_TIMEOUT_SECONDS: float = Field(default=60.0, gt=0, allow_inf_nan=False)

    @field_validator("LLM_PROVIDER", mode="before")
    @classmethod
    def _blank_llm_provider_means_runpod(cls, value: object) -> object:
        if value is None or (isinstance(value, str) and not value.strip()):
            return "runpod"
        return value.strip() if isinstance(value, str) else value

    RUNPOD_API_KEY: Optional[SecretStr] = None
    RUNPOD_ENDPOINT_ID: Optional[str] = None  # identifier, not a secret
    TREND_SOURCE_API_KEY: Optional[SecretStr] = None

    # Milestone 11B: CV PDF -> GLM-5.3 extraction. Deliberately separate
    # from RUNPOD_ENDPOINT_ID above (f0phohhegtydji) — that ID belongs to
    # Hussain's embedding provider (app/services/hussain_matching); mixing
    # the two would risk a future config change to one silently breaking
    # the other. The GLM endpoint is addressed via a full base URL
    # (RunPod's OpenAI-compatible route already encodes its own endpoint
    # ID), not a second bare RUNPOD_ENDPOINT_ID-style variable. The API
    # key is shared (same RunPod account) — RUNPOD_API_KEY above.
    RUNPOD_GLM_BASE_URL: str = "https://api.runpod.ai/v2/b1dd8hy2hqo1nb/openai/v1"
    RUNPOD_GLM_MODEL: str = "glm-5.3"
    # Controlled read-phase experiment only; not an overall request deadline.
    RUNPOD_GLM_READ_TIMEOUT_SECONDS: float = Field(
        default=30.0, gt=0, le=40, allow_inf_nan=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
