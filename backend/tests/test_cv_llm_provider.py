"""Offline regression coverage for CV extraction provider selection."""
from __future__ import annotations

import json
from unittest.mock import patch

import httpx

from app.core.config import Settings
from app.services import cv_extraction_service
from app.services.cv_pdf import PdfExtractionResult
from app.services.glm_client import extract_cv_fields
from app.services.hussain_matching.runpod_client import runpod_configured


def _extract_through_mock_transport(settings: Settings, cv_text: str) -> tuple[dict, list[str]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps({"name": "Jane Student"})}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with patch(
            "app.services.cv_extraction_service.extract_cv_fields",
            side_effect=lambda text, **kwargs: extract_cv_fields(text, client=client, **kwargs),
        ):
            data, warnings = cv_extraction_service.run_cv_extraction(
                PdfExtractionResult(text=cv_text, page_count=1, has_extractable_text=True),
                settings,
            )
    finally:
        client.close()
    assert len(requests) == 1
    return {"data": data, "warnings": warnings, "request": requests[0]}


def test_openrouter_cv_extraction_uses_only_openrouter_settings(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_API_KEY", "synthetic-openrouter-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("LLM_MODEL", "z-ai/glm-5.3-flashx")
    monkeypatch.setenv("RUNPOD_API_KEY", "synthetic-runpod-key")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "synthetic-embedding-endpoint")
    monkeypatch.setenv("RUNPOD_GLM_BASE_URL", "https://runpod.invalid/v1")
    monkeypatch.setenv("RUNPOD_GLM_MODEL", "runpod-glm-model")

    settings = Settings(_env_file=None)
    result = _extract_through_mock_transport(settings, "Python developer with SQL experience.")

    request = result["request"]
    payload = json.loads(request.content)
    assert request.url.host == "openrouter.ai"
    assert request.url.path == "/api/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer synthetic-openrouter-key"
    assert payload["model"] == "z-ai/glm-5.3-flashx"
    assert payload["reasoning"] == {"effort": "low"}
    assert payload["max_tokens"] == 2_500
    assert "reasoning_effort" not in payload
    assert result["data"].status == "ok"


def test_runpod_cv_extraction_stays_separate_from_openrouter(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "synthetic-openrouter-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.invalid/v1")
    monkeypatch.setenv("LLM_MODEL", "openrouter-model")
    monkeypatch.setenv("RUNPOD_API_KEY", "synthetic-runpod-key")
    monkeypatch.setenv("RUNPOD_GLM_BASE_URL", "https://runpod.invalid/v1")
    monkeypatch.setenv("RUNPOD_GLM_MODEL", "runpod-glm-model")
    settings = Settings(LLM_PROVIDER="runpod", _env_file=None)

    result = _extract_through_mock_transport(settings, "Python developer with SQL experience.")

    request = result["request"]
    payload = json.loads(request.content)
    assert request.url.host == "runpod.invalid"
    assert request.headers["authorization"] == "Bearer synthetic-runpod-key"
    assert payload["model"] == "runpod-glm-model"
    assert payload["reasoning_effort"] == "low"
    assert "reasoning" not in payload
    assert result["data"].status == "ok"


def test_missing_openrouter_settings_fail_closed_without_using_runpod(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("RUNPOD_API_KEY", "synthetic-runpod-key")
    settings = Settings(_env_file=None)

    with patch("app.services.cv_extraction_service.extract_cv_fields") as extract:
        data, warnings = cv_extraction_service.run_cv_extraction(
            PdfExtractionResult(
                text="Technical Skills: Python, SQL",
                page_count=1,
                has_extractable_text=True,
            ),
            settings,
        )

    extract.assert_not_called()
    assert data.status == "manual_review"
    assert data.draft.suggested_profile.skills == []
    assert {item.name.lower() for item in data.draft.skills_requiring_review} >= {"python", "sql"}
    assert warnings == [cv_extraction_service.MANUAL_REVIEW_WARNING]


def test_embedding_configuration_only_uses_runpod_credentials(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_API_KEY", "synthetic-openrouter-key")
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    assert runpod_configured() is False

    monkeypatch.setenv("RUNPOD_API_KEY", "synthetic-runpod-key")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "synthetic-embedding-endpoint")
    assert runpod_configured() is True
