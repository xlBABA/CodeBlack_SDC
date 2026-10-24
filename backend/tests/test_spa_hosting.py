"""Milestone 9B: SPA static hosting (app/spa.py), mounted from app.main.

Covers: HTML entrypoint, static assets, deep-link fallback, and that
/api/v1, /docs and /openapi.json are preserved exactly — both when a
frontend build is present and when it is absent.

Milestone 9E: the real-app checks below never assume whether
frontend/dist currently exists on disk — that varies by checkout (a
plain backend-only checkout has none; an integration worktree that has
already run `npm run build` does). Each check instead reads the actual
filesystem state via app.main.FRONTEND_DIST_DIR and asserts the response
is consistent with *that*, so the suite passes identically either way.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.main as main_module
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


# --- Path traversal: files outside dist_dir are never served -----------------


def _write_outside_dist_secret(tmp_path: Path) -> Path:
    secret = tmp_path / "secret.txt"
    secret.write_text("outside-dist-secret", encoding="utf-8")
    return secret


@pytest.mark.parametrize(
    "path",
    [
        "/..%2fsecret.txt",
        "/%2e%2e%2fsecret.txt",
        "/%2E%2E%2Fsecret.txt",
        "/..%5csecret.txt",
        "/..%5c..%5csecret.txt",
    ],
)
def test_encoded_parent_segments_never_escape_dist(
    spa_client: TestClient, tmp_path: Path, path: str
):
    _write_outside_dist_secret(tmp_path)
    response = spa_client.get(path)
    assert "outside-dist-secret" not in response.text
    assert response.status_code == 200
    assert "mustaqbal-ai-spa" in response.text


def test_parent_segments_under_assets_mount_never_escape_dist(
    spa_client: TestClient, tmp_path: Path
):
    _write_outside_dist_secret(tmp_path)
    response = spa_client.get("/assets%2f..%2f..%2fsecret.txt")
    assert "outside-dist-secret" not in response.text
    assert response.status_code == 404


def test_absolute_path_never_escapes_dist(spa_client: TestClient, tmp_path: Path):
    secret = _write_outside_dist_secret(tmp_path)
    response = spa_client.get("/" + str(secret).replace("/", "%2f"))
    assert "outside-dist-secret" not in response.text
    assert "mustaqbal-ai-spa" in response.text


def test_symlink_pointing_outside_dist_is_not_served(
    spa_client: TestClient, tmp_path: Path
):
    secret = _write_outside_dist_secret(tmp_path)
    (tmp_path / "dist" / "linked.txt").symlink_to(secret)
    response = spa_client.get("/linked.txt")
    assert "outside-dist-secret" not in response.text
    assert "mustaqbal-ai-spa" in response.text


def test_file_inside_dist_subdirectory_is_still_served(
    spa_client: TestClient, tmp_path: Path
):
    nested = tmp_path / "dist" / "sdg"
    nested.mkdir()
    (nested / "goal.txt").write_text("inside-dist", encoding="utf-8")
    response = spa_client.get("/sdg/goal.txt")
    assert response.status_code == 200
    assert response.text == "inside-dist"


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


def test_frontend_dist_dir_points_at_repo_root_frontend_dist():
    """main.py's FRONTEND_DIST_DIR must resolve to repo_root/frontend/dist,
    a sibling of the backend/ checkout — checked structurally, never by
    asserting whether that directory currently exists (see module docstring)."""
    backend_dir = Path(main_module.__file__).resolve().parent.parent  # backend/
    expected = backend_dir.parent / "frontend" / "dist"  # repo_root/frontend/dist
    assert main_module.FRONTEND_DIST_DIR == expected


def test_real_app_spa_mount_is_consistent_with_actual_dist_presence(client: TestClient):
    """Uses the shared app.main.app via the existing `client` fixture.
    Reads whether frontend/dist/index.html actually exists on disk in
    *this* checkout, then asserts the real app's behavior matches that
    state — 200 SPA HTML if a build is present, the original 404 if not.
    Passes identically on a backend-only checkout and on an integration
    worktree with a real frontend build, unlike the fragile "it never
    exists" assumption this replaces."""
    assert client.get("/api/v1/health").status_code == 200

    dist_build_present = (main_module.FRONTEND_DIST_DIR / "index.html").is_file()
    root = client.get("/")
    if dist_build_present:
        assert root.status_code == 200
        assert "text/html" in root.headers["content-type"]
    else:
        assert root.status_code == 404
        assert root.json() == {"detail": "Not Found"}
