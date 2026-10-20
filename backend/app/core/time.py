"""Shared UTC timestamp helpers — ISO 8601 with trailing Z, per CLAUDE.md date rules."""
from datetime import datetime, timezone


def to_utc_z(value: datetime) -> str:
    """Format a timezone-aware datetime as UTC ISO 8601 with a trailing Z
    (not Python's default "+00:00" offset), matching the rest of this API."""
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_now_iso() -> str:
    return to_utc_z(datetime.now(timezone.utc))
