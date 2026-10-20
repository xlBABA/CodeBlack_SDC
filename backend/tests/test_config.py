from app.core.config import Settings


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
