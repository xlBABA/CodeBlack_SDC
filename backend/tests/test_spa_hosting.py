"""Milestone 9B: SPA static hosting (app/spa.py), mounted from app.main.

Covers: HTML entrypoint, static assets, deep-link fallback, and that
/api/v1, /docs and /openapi.json are preserved exactly — both when a
frontend build is present and (against the real app, since no frontend
build exists on this branch) when it is absent.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.router import api_router
from app.core.errors import register_exception_handlers
from app.spa import mount_spa


def _build_fake_dist(tmp_path: Path) -> Path:
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text(
        "<!doctype html><html><body><div id='root'>mustaqbal-ai-spa</div></body></html>",
        encoding="utf-8",
    )
    (dist_dir / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")
    (assets_dir / "index-abc123.js").write_text("console.log('spa');", encoding="utf-8")
    return dist_dir


@pytest.fixture
def spa_client(tmp_path: Path) -> TestClient:
    """A standalone app carrying the real api_router plus a fake SPA build —
    never the shared app.main.app singleton, so no route leaks into other
    test modules."""
    dist_dir = _build_fake_dist(tmp_path)
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    mount_spa(app, dist_dir)
    return TestClient(app)


# --- HTML entrypoint -------------------------------------------------------


def test_root_serves_spa_index_html(spa_client: TestClient):
    response = spa_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "mustaqbal-ai-spa" in response.text


# --- Static assets ----------------------------------------------------------


def test_hashed_asset_file_is_served_directly(spa_client: TestClient):
    response = spa_client.get("/assets/index-abc123.js")
    assert response.status_code == 200
    assert "spa" in response.text


def test_top_level_static_file_is_served_directly(spa_client: TestClient):
    response = spa_client.get("/favicon.svg")
    assert response.status_code == 200
    assert "<svg" in response.text


# --- SPA deep-link fallback (history-mode routing) --------------------------


@pytest.mark.parametrize(
    "path",
    ["/dashboard", "/start", "/roles/data_analyst", "/methodology", "/some/deeply/nested/unknown/route"],
)
def test_deep_link_falls_back_to_index_html(spa_client: TestClient, path: str):
    response = spa_client.get(path)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "mustaqbal-ai-spa" in response.text


# --- API route preservation (SPA mounted) ------------------------------------


def test_health_route_unaffected_by_spa_mount(spa_client: TestClient):
    response = spa_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_api_v1_path_returns_plain_404_not_spa_html(spa_client: TestClient):
    response = spa_client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert "text/html" not in response.headers["content-type"]


def test_docs_and_openapi_unaffected_by_spa_mount(spa_client: TestClient):
    docs = spa_client.get("/docs")
    assert docs.status_code == 200
    openapi = spa_client.get("/openapi.json")
    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"]


# --- Missing-dist behavior (mount_spa is a no-op) ----------------------------


def test_mount_spa_is_a_no_op_when_dist_directory_does_not_exist(tmp_path: Path):
    missing_dist = tmp_path / "does-not-exist" / "dist"
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    mount_spa(app, missing_dist)  # must not raise

    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    root = client.get("/")
    assert root.status_code == 404
    assert root.json() == {"detail": "Not Found"}


def test_mount_spa_is_a_no_op_when_dist_exists_but_index_html_is_missing(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "assets").mkdir()
    # No index.html written — an incomplete/partial build must not be served.
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    mount_spa(app, dist_dir)  # must not raise

    client = TestClient(app)
    assert client.get("/").status_code == 404


def test_real_app_is_unaffected_because_no_frontend_build_exists_on_this_branch(client: TestClient):
    """Uses the shared app.main.app via the existing `client` fixture —
    frontend/dist genuinely does not exist on this branch, so this proves
    requirement 4 against the real app, not a simulation."""
    assert client.get("/api/v1/health").status_code == 200
    root = client.get("/")
    assert root.status_code == 404
    assert root.json() == {"detail": "Not Found"}
