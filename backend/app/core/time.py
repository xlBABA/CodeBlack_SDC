"""Shared UTC timestamp helper — ISO 8601 with trailing Z, per CLAUDE.md date rules."""
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
