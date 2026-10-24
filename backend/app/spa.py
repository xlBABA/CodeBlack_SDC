"""Serves a built Vite/React SPA (frontend/dist) from the app root.

Build prerequisite (not performed here — see requirement to never build at
Python runtime): run `npm run build` inside `frontend/` first, which
produces `frontend/dist/index.html` plus a `frontend/dist/assets/` folder.
This module only serves whatever is already on disk.

mount_spa() is a pure add-on called from app.main after the API router is
registered. When `dist_dir/index.html` doesn't exist (no frontend build —
e.g. a clean backend-only checkout), it does nothing at all: no new route
is registered, and the app behaves exactly as an API-only backend would
without this module ever being imported.

Unknown /api/v1/* paths, and the reserved /docs, /openapi.json, /redoc
paths, always fall through to FastAPI's own "Not Found" handling
(`{"detail": "Not Found"}`, 404) instead of ever being served SPA HTML —
the same response they'd get with no SPA mounted at all. In practice the
three reserved literal paths are already matched by FastAPI's own
built-in routes (registered before this module ever runs) before reaching
the catch-all below; the explicit check here is a defensive second layer,
not the only thing preventing it.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_RESERVED_TOP_LEVEL_PATHS = {"docs", "openapi.json", "redoc"}


def _is_reserved_path(full_path: str) -> bool:
    first_segment = full_path.split("/", 1)[0]
    return first_segment == "api" or full_path in _RESERVED_TOP_LEVEL_PATHS


def mount_spa(app: FastAPI, dist_dir: Path) -> None:
    index_file = dist_dir / "index.html"
    if not index_file.is_file():
        return

    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="spa-assets")

    dist_root = dist_dir.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_entrypoint(full_path: str) -> FileResponse:
        if _is_reserved_path(full_path):
            raise HTTPException(status_code=404)

        # Only files that resolve inside the build directory are served
        # directly. "../" segments (including percent-encoded ones),
        # absolute paths and symlinks pointing outside dist_dir resolve
        # elsewhere and fall through to index.html instead.
        candidate = (dist_root / full_path).resolve()
        if full_path and candidate.is_relative_to(dist_root) and candidate.is_file():
            return FileResponse(candidate)

        # Any other path ("", "dashboard", "roles/data_analyst", ...) is a
        # client-side route — the SPA's own router resolves it in the
        # browser once index.html loads (history-mode deep-link fallback).
        return FileResponse(index_file)
