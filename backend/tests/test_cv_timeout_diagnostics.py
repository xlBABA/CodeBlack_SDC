"""Synthetic, network-denied regressions for the real PDF -> HTTP pipeline."""
import asyncio
import json
import logging
import threading
import time
from pathlib import Path

import httpx
import pytest

from app.core.config import Settings, get_settings
from app.db.models import StudentProfileORM
from app.main import app
from app.services import glm_client
from app.services.glm_client import GlmExtractionError, GlmExtractionResult
from tests.test_cv_parse import FAKE_GLM_JSON, VALID_PDF, _build_text_pdf


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Real outbound HTTP is forbidden")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked)


def install_provider(monkeypatch, handler):
    """Use the real GLM client, replacing only its owned transport."""
    client_type = httpx.Client
    clients = []

    def factory(**kwargs):
        client = client_type(transport=httpx.MockTransport(handler), **kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr(glm_client.httpx, "Client", factory)
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, RUNPOD_API_KEY="synthetic-secret",
        RUNPOD_GLM_BASE_URL="https://synthetic.invalid/v1",
        RUNPOD_GLM_MODEL="synthetic-model",
    )
    return clients


@pytest.mark.parametrize("length", [100, 11_000, 15_000])
def test_synthetic_pdf_payload_and_seven_fields(client, db_session, monkeypatch, length):
    text = ("Python SQL synthetic CV " * 700)[:length]
    calls = []

    def handler(request):
        calls.append(request)
        payload = json.loads(request.content)
        assert str(request.url) == "https://synthetic.invalid/v1/chat/completions"
        assert payload["model"] == "synthetic-model"
        assert payload["messages"][1]["content"] == text.strip()[:12_000]
        assert payload["max_tokens"] == 1200
        assert payload["temperature"] == 0
        assert payload["reasoning_effort"] == "low"
        assert payload["response_format"] == {"type": "json_object"}
        assert request.extensions["timeout"] == dict.fromkeys(
            ["connect", "read", "write", "pool"], 30.0
        )
        return httpx.Response(200, json={
            "choices": [{"message": {"content": json.dumps(FAKE_GLM_JSON)}}]
        })

    clients = install_provider(monkeypatch, handler)
    response = client.post("/api/v1/cv/parse", files={
        "file": ("synthetic.pdf", _build_text_pdf(text), "application/pdf"),
    })
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"data", "data_mode", "generated_at", "warnings"}
    assert body["data"]["status"] == "ok"
    draft = body["data"]["draft"]
    for key in ("name", "summary", "education", "projects", "experience", "certifications"):
        assert key in draft
    assert {s["skill_id"] for s in draft["mapped_skills"]} == {"python", "sql"}
    assert len(calls) == 1
    assert all(c.is_closed for c in clients)
    assert db_session.query(StudentProfileORM).count() == 0


@pytest.mark.parametrize("category", [
    httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout,
])
def test_real_timeout_categories_safe_fallback(
    client, db_session, monkeypatch, caplog, category,
):
    calls = []

    def handler(request):
        calls.append(request)
        raise category("PRIVATE provider body synthetic-secret", request=request)

    clients = install_provider(monkeypatch, handler)
    caplog.set_level(logging.INFO)
    started = time.monotonic()
    response = client.post("/api/v1/cv/parse", files={
        "file": ("PRIVATE-filename.pdf", _build_text_pdf(
            "Technical Skills: Python, SQL, JavaScript"
        ), "application/pdf"),
    })
    elapsed = time.monotonic() - started
    assert elapsed < 2
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "manual_review"
    assert data["draft"]["suggested_profile"]["skills"] == []
    assert data["draft"]["mapped_skills"] == []
    assert {"Python", "SQL"} <= {
        s["name"] for s in data["draft"]["skills_requiring_review"]
    }
    assert db_session.query(StudentProfileORM).count() == 0
    assert len(calls) == 1
    assert all(c.is_closed for c in clients)
    assert f"category={category.__name__}" in caplog.text
    assert "pdf_elapsed_ms=" in caplog.text
    assert "elapsed_ms=" in caplog.text
    for private in ("PRIVATE", "synthetic-secret", "Technical Skills:", "JavaScript"):
        assert private not in caplog.text


@pytest.mark.parametrize("phase", ["pdf", "provider"])
def test_slow_phase_does_not_block_other_requests(client, monkeypatch, phase):
    import app.api.v1.endpoints.cv as endpoint
    entered = threading.Event()
    release = threading.Event()
    original = endpoint.validate_and_extract

    def slow(*args):
        entered.set()
        assert release.wait(3), "event loop was blocked"
        if phase == "pdf":
            return original(*args)
        raise GlmExtractionError("The extraction service timed out.")

    monkeypatch.setattr(endpoint, "validate_and_extract", slow if phase == "pdf" else original)
    import app.services.cv_extraction_service as service
    monkeypatch.setattr(
        service, "extract_cv_fields",
        slow if phase == "provider" else lambda *a, **k: GlmExtractionResult(FAKE_GLM_JSON),
    )
    # Accept provider keyword arguments while retaining the blocking event.
    if phase == "provider":
        monkeypatch.setattr(service, "extract_cv_fields", lambda *a, **k: slow(*a))

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test",
        ) as http:
            upload = asyncio.create_task(http.post("/api/v1/cv/parse", files={
                "file": ("synthetic.pdf", VALID_PDF, "application/pdf"),
            }))
            try:
                deadline = time.monotonic() + 1
                while not entered.is_set() and time.monotonic() < deadline:
                    await asyncio.sleep(.005)
                assert entered.is_set()
                started = time.monotonic()
                health = await asyncio.wait_for(http.get("/api/v1/health"), .5)
                assert health.status_code == 200
                assert time.monotonic() - started < .5
                assert not upload.done()
            finally:
                release.set()
            result = await asyncio.wait_for(upload, 2)
            assert result.json()["data"]["status"] == (
                "ok" if phase == "pdf" else "manual_review"
            )
    asyncio.run(scenario())


def test_frontend_confirmation_contract_remains_explicit():
    """Source-level safeguard; not a substitute for browser interaction tests."""
    root = Path(__file__).resolve().parents[2]
    review = (root / "frontend/src/components/intake/cv-review.tsx").read_text()
    assert "const [confirmed, setConfirmed] = useState(false)" in review
    assert "disabled={!confirmed || !ready || submitting}" in review
    assert "skills: suggested.skills.filter" in review
    api = (root / "frontend/src/lib/api.ts").read_text()
    assert "const UPLOAD_TIMEOUT_MS = 60_000" in api
