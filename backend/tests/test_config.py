import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_glm_read_timeout_default():
    assert Settings(_env_file=None).RUNPOD_GLM_READ_TIMEOUT_SECONDS == 30.0


@pytest.mark.parametrize("value", ["40", "30", "0.5"])
def test_glm_read_timeout_environment(monkeypatch, value):
    monkeypatch.setenv("RUNPOD_GLM_READ_TIMEOUT_SECONDS", value)
    assert Settings(_env_file=None).RUNPOD_GLM_READ_TIMEOUT_SECONDS == float(value)


@pytest.mark.parametrize("value", [
    "", " ", "invalid", "0", "-1", "nan", "NaN", "inf", "-inf", "1e999", "40.01", "41",
])
def test_glm_read_timeout_invalid_environment(monkeypatch, value):
    monkeypatch.setenv("RUNPOD_GLM_READ_TIMEOUT_SECONDS", value)
    with pytest.raises(ValidationError, match="RUNPOD_GLM_READ_TIMEOUT_SECONDS"):
        Settings(_env_file=None)


def test_catalog_mode_defaults_to_fixture():
    assert Settings(_env_file=None).CATALOG_MODE == "fixture"


def test_catalog_mode_accepts_cached():
    assert Settings(CATALOG_MODE="cached", _env_file=None).CATALOG_MODE == "cached"


def test_invalid_catalog_mode_is_rejected():
    with pytest.raises(ValidationError):
        Settings(CATALOG_MODE="live", _env_file=None)


def test_catalog_mode_is_independent_of_enable_fixtures():
    """Two separate settings: one gates the scoring provider, the other
    the role/skill data provider. Neither implies the other."""
    settings = Settings(CATALOG_MODE="cached", ENABLE_FIXTURES=False, _env_file=None)
    assert settings.CATALOG_MODE == "cached"
    assert settings.ENABLE_FIXTURES is False


def test_matching_mode_defaults_to_fixture():
    assert Settings(_env_file=None).MATCHING_MODE == "fixture"


def test_matching_mode_accepts_hussain():
    assert Settings(MATCHING_MODE="hussain", _env_file=None).MATCHING_MODE == "hussain"


def test_invalid_matching_mode_is_rejected():
    with pytest.raises(ValidationError):
        Settings(MATCHING_MODE="live", _env_file=None)


def test_matching_mode_is_independent_of_catalog_mode_and_enable_fixtures():
    settings = Settings(MATCHING_MODE="hussain", CATALOG_MODE="cached", ENABLE_FIXTURES=False, _env_file=None)
    assert settings.MATCHING_MODE == "hussain"
    assert settings.CATALOG_MODE == "cached"
    assert settings.ENABLE_FIXTURES is False


def test_settings_load_without_ai_credentials(monkeypatch):
    for var in (
        "LLM_PROVIDER",
        "LLM_API_KEY",
        "RUNPOD_API_KEY",
        "RUNPOD_ENDPOINT_ID",
        "TREND_SOURCE_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.LLM_API_KEY is None
    assert settings.RUNPOD_API_KEY is None
    assert settings.DATABASE_URL.startswith("sqlite")


@pytest.mark.parametrize("value", [None, "", "   "])
def test_blank_llm_provider_preserves_runpod_default(value):
    assert Settings(LLM_PROVIDER=value, _env_file=None).LLM_PROVIDER == "runpod"


def test_llm_provider_settings_load_from_environment_without_exposing_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_API_KEY", "synthetic-openrouter-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("LLM_MODEL", "z-ai/glm-5.3-flashx")
    monkeypatch.setenv("RUNPOD_API_KEY", "synthetic-runpod-key")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "synthetic-embedding-endpoint")

    settings = Settings(_env_file=None)

    assert settings.LLM_PROVIDER == "openrouter"
    assert settings.LLM_API_KEY is not None
    assert settings.LLM_BASE_URL == "https://openrouter.ai/api/v1"
    assert settings.LLM_MODEL == "z-ai/glm-5.3-flashx"
    assert settings.RUNPOD_API_KEY is not None
    assert settings.RUNPOD_ENDPOINT_ID == "synthetic-embedding-endpoint"
    assert "synthetic-openrouter-key" not in repr(settings)
    assert "synthetic-runpod-key" not in repr(settings)


def test_invalid_llm_provider_is_rejected():
    with pytest.raises(ValidationError):
        Settings(LLM_PROVIDER="other", _env_file=None)


def test_llm_timeout_must_be_positive_and_finite():
    for value in ("0", "-1", "nan", "inf"):
        with pytest.raises(ValidationError, match="LLM_TIMEOUT_SECONDS"):
            Settings(LLM_TIMEOUT_SECONDS=value, _env_file=None)
