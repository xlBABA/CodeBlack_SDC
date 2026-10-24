"""LLM_PROVIDER selection for POST /api/v1/cv/parse.

Every test points the selected provider at a local fake OpenAI-compatible
server (tests/fake_llm_server.py), so the real glm_client request is
built and sent, but never leaves 127.0.0.1. Credentials are dummy
strings, never real keys.
"""
from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.services.cv_extraction_service import CV_UNAVAILABLE_WARNING
from app.services.hussain_matching.runpod_client import runpod_configured
from tests.fake_llm_server import fake_llm_server
from tests.test_cv_parse import FAKE_GLM_JSON, VALID_PDF, _clear_override, _override_settings, _post_cv

RUNPOD_DUMMY_KEY = "runpod-dummy-key"
LLM_DUMMY_KEY = "llm-dummy-key"


@pytest.fixture(autouse=True)
def _restore_settings():
    yield
    _clear_override()


def _openrouter_settings(base_url: str, **overrides) -> dict:
    settings = {
        "LLM_PROVIDER": "openrouter",
        "LLM_API_KEY": LLM_DUMMY_KEY,
        "LLM_BASE_URL": base_url,
        "LLM_MODEL": "vendor/model-x",
        # A RunPod key is present on purpose: openrouter must never use it.
        "RUNPOD_API_KEY": RUNPOD_DUMMY_KEY,
    }
    settings.update(overrides)
    return settings


# --- Settings ------------------------------------------------------------------


@pytest.mark.parametrize("value", [None, "", "   "])
def test_unset_or_blank_llm_provider_means_runpod(value):
    assert Settings(LLM_PROVIDER=value, _env_file=None).LLM_PROVIDER == "runpod"


def test_llm_timeout_defaults_to_60_seconds():
    assert Settings(_env_file=None).LLM_TIMEOUT_SECONDS == 60.0


def test_unknown_llm_provider_fails_loudly():
    with pytest.raises(ValidationError):
        Settings(LLM_PROVIDER="openai", _env_file=None)


# --- Provider selection ----------------------------------------------------------


def test_default_runpod_provider_is_unchanged(client: TestClient):
    with fake_llm_server(json.dumps(FAKE_GLM_JSON)) as runpod, fake_llm_server("{}") as other:
        _override_settings(
            RUNPOD_API_KEY=RUNPOD_DUMMY_KEY,
            RUNPOD_GLM_BASE_URL=runpod.base_url,
            RUNPOD_GLM_MODEL="glm-5.3",
            LLM_API_KEY=LLM_DUMMY_KEY,
            LLM_BASE_URL=other.base_url,
            LLM_MODEL="vendor/model-x",
        )
        response = _post_cv(client, VALID_PDF)

    assert response.json()["data"]["status"] == "ok"
    assert other.requests == []
    (request,) = runpod.requests
    assert request["path"] == "/v1/chat/completions"
    assert request["authorization"] == f"Bearer {RUNPOD_DUMMY_KEY}"
    assert request["body"]["model"] == "glm-5.3"
    assert request["body"]["reasoning_effort"] == "low"
    assert request["body"]["response_format"] == {"type": "json_object"}
    assert request["body"]["temperature"] == 0.0


def test_openrouter_provider_uses_only_llm_settings(client: TestClient):
    with fake_llm_server(json.dumps(FAKE_GLM_JSON)) as openrouter, fake_llm_server("{}") as runpod:
        _override_settings(**_openrouter_settings(openrouter.base_url, RUNPOD_GLM_BASE_URL=runpod.base_url))
        response = _post_cv(client, VALID_PDF)

    body = response.json()
    assert body["data"]["status"] == "ok"
    assert {s["skill_id"] for s in body["data"]["draft"]["mapped_skills"]} == {"python", "sql"}
    assert runpod.requests == []
    (request,) = openrouter.requests
    assert request["path"] == "/v1/chat/completions"
    assert request["authorization"] == f"Bearer {LLM_DUMMY_KEY}"
    assert request["body"]["model"] == "vendor/model-x"
    assert "reasoning_effort" not in request["body"]
    assert request["body"]["response_format"] == {"type": "json_object"}
    assert request["body"]["temperature"] == 0.0


@pytest.mark.parametrize("missing", ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"])
def test_openrouter_with_a_missing_setting_never_falls_back_to_runpod(client: TestClient, caplog, missing):
    with fake_llm_server(json.dumps(FAKE_GLM_JSON)) as openrouter, fake_llm_server(json.dumps(FAKE_GLM_JSON)) as runpod:
        settings = _openrouter_settings(openrouter.base_url, RUNPOD_GLM_BASE_URL=runpod.base_url)
        settings[missing] = None
        _override_settings(**settings)
        with caplog.at_level(logging.WARNING, logger="app.services.cv_extraction_service"):
            response = _post_cv(client, VALID_PDF)

    body = response.json()
    assert response.status_code == 200
    assert body["data"]["status"] == "manual_review"
    assert body["warnings"] == [CV_UNAVAILABLE_WARNING]
    assert body["data"]["extracted_text_preview"]  # the student can still copy from the text
    assert openrouter.requests == [] and runpod.requests == []  # no request to either endpoint
    log = caplog.text
    assert missing in log and "LLM_PROVIDER=openrouter" in log
    assert LLM_DUMMY_KEY not in log and RUNPOD_DUMMY_KEY not in log


def test_openrouter_timeout_is_configurable(client: TestClient):
    with fake_llm_server(json.dumps(FAKE_GLM_JSON), delay_seconds=1.0) as openrouter:
        _override_settings(**_openrouter_settings(openrouter.base_url, LLM_TIMEOUT_SECONDS=0.2))
        response = _post_cv(client, VALID_PDF)

    assert response.json()["data"]["status"] == "manual_review"


def test_openrouter_rejected_key_falls_back_without_logging_it(client: TestClient, caplog):
    with fake_llm_server("{}", status=401) as openrouter:
        _override_settings(**_openrouter_settings(openrouter.base_url))
        with caplog.at_level(logging.WARNING):
            response = _post_cv(client, VALID_PDF)

    assert response.json()["data"]["status"] == "manual_review"
    assert "LLM_API_KEY" in caplog.text
    assert LLM_DUMMY_KEY not in caplog.text


# --- Embeddings are unaffected ---------------------------------------------------


def test_embeddings_still_read_only_runpod_credentials(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_API_KEY", LLM_DUMMY_KEY)
    assert runpod_configured() is False  # an LLM key never enables RunPod embeddings

    monkeypatch.setenv("RUNPOD_API_KEY", RUNPOD_DUMMY_KEY)
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "dummyendpoint")
    assert runpod_configured() is True


def test_matching_is_unchanged_by_the_cv_provider(client: TestClient):
    profile = {"interests": [], "skills": [{"skill_id": "python", "name": "Python"}], "projects": []}
    results = []
    for provider in ("runpod", "openrouter"):
        _override_settings(
            CATALOG_MODE="cached", MATCHING_MODE="hussain", LLM_PROVIDER=provider, LLM_API_KEY=LLM_DUMMY_KEY
        )
        results.append(client.post("/api/v1/careers/match", json={"profile": profile}).json()["data"]["matches"])
    assert results[0] == results[1]
