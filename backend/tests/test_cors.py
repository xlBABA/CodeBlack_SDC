import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app


def test_allowed_origin_receives_cors_header(client: TestClient):
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_disallowed_origin_receives_no_cors_header(client: TestClient):
    response = client.get("/api/v1/health", headers={"Origin": "http://evil.example.com"})
    # The request itself still succeeds at the HTTP level (Starlette's
    # CORSMiddleware doesn't block simple requests), but without the
    # allow-origin header a browser refuses to let the calling page read
    # the response — that's the actual enforcement point.
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_allowed_origin_preflight_succeeds(client: TestClient):
    response = client.options(
        "/api/v1/careers/match",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_disallowed_origin_preflight_is_rejected(client: TestClient):
    response = client.options(
        "/api/v1/careers/match",
        headers={"Origin": "http://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_multiple_configured_origins_are_all_recognized():
    settings = Settings(CORS_ORIGINS="http://localhost:5173,https://app.example.com", _env_file=None)
    assert settings.cors_origins_list == ["http://localhost:5173", "https://app.example.com"]


def test_wildcard_cors_origin_is_rejected(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_wildcard_among_multiple_origins_is_also_rejected():
    with pytest.raises(ValidationError):
        Settings(CORS_ORIGINS="http://localhost:5173,*", _env_file=None)


def test_app_always_sends_allow_credentials_true():
    """Documents the invariant the wildcard-rejection validator exists to
    protect: credentials are always on, so '*' origins must stay banned."""
    cors_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )
    assert cors_middleware.kwargs["allow_credentials"] is True
