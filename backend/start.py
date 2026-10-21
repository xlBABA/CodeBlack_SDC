"""Local/Replit-compatible startup launcher.

Preserves `app.main:app` as the importable ASGI target (the existing
`uvicorn app.main:app --reload` manual command keeps working exactly as
before, unaffected by this file) — this is an additional, optional entry
point that resolves PORT/host/reload consistently for a non-interactive
deployment context, without hardcoding any deployment-specific URL.

Local Windows dev:
    backend\\.venv\\Scripts\\python.exe start.py

Future Replit run command (not yet configured/deployed anywhere — see
DEPLOYMENT.md):
    python start.py
"""
from __future__ import annotations

import os


def resolve_port(env: dict[str, str] | None = None) -> int:
    """PORT is set by the hosting platform (e.g. Replit); 8000 is only a
    local-dev fallback, never a deployment assumption. Must be a valid
    TCP port (1-65535) — anything outside that range fails clearly here
    rather than failing later with a less obvious socket/uvicorn error."""
    env = os.environ if env is None else env
    raw = env.get("PORT", "8000")
    try:
        port = int(raw)
    except ValueError:
        raise ValueError(f"PORT must be an integer, got {raw!r}") from None
    if not (1 <= port <= 65535):
        raise ValueError(f"PORT must be between 1 and 65535, got {port}")
    return port


def should_reload(env: dict[str, str] | None = None) -> bool:
    """Reload is enabled only when ENVIRONMENT is explicitly set to the
    literal string "development" — never by an implicit default. Unset,
    empty, or any other value (including "production", a typo, or a
    forgotten variable) fails safe to reload=False. Local development
    must opt in explicitly (e.g. via .env) to get reload through this
    launcher; the existing manual `uvicorn app.main:app --reload` command
    is unaffected by this function and keeps working as before."""
    env = os.environ if env is None else env
    return env.get("ENVIRONMENT") == "development"


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=resolve_port(),
        reload=should_reload(),
    )


if __name__ == "__main__":
    main()
