"""Cached GitHub-derived trend snapshot dataset — Jawad's verified
trend_snapshots/*.json (app/data/cached/trend_snapshots/; byte-identical
copies of feat/jawad-trends-data:data/trend_snapshots/*.json as of commit
2838340).

Milestone 6D-2A scope: import and validation ONLY — see
resource_catalog_cached.py's module docstring for the same disclaimer.
Nothing here is wired into GET /trends or MatchingService; no
TrendProvider is implemented.

SCHEMA BOUNDARY (documented here, NOT implemented — see the Milestone
6D-2A report): Jawad's source_status values are live|cached|unavailable.
Our public contract (app/schemas/trends.py: SourceStatus =
Literal["ok", "stale", "unavailable"]) only accepts ok|stale|unavailable
— neither "live" nor "cached" is valid there. A future activation phase
must translate between these two enums; this module deliberately
validates against JAWAD'S OWN enum only and never touches
app.schemas.trends or any public response.

Each snapshot file also carries no "direction" field at all — rising/
falling/stable/unknown is computed at read time by Jawad's own
aggregate.py from current vs. previous total_count, not stored on disk.
This module does not reimplement that computation (that would be
activation logic, out of scope here) — it validates only the stored
fields.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.services.role_catalog_cached import CachedCatalogError, _load_json, _require_dict

_TREND_SNAPSHOTS_DIR = Path(__file__).resolve().parents[1] / "data" / "cached" / "trend_snapshots"

# Jawad's own source_status enum — distinct from, and not yet mapped to,
# the public contract's ok|stale|unavailable (see module docstring).
_JAWAD_SOURCE_STATUSES = {"live", "cached", "unavailable"}

_REQUIRED_SNAPSHOT_FIELDS = {"skill_id", "source_status", "source_id", "current", "previous", "prior_snapshot"}
_REQUIRED_WINDOW_FIELDS = {"topic", "start", "end", "total_count", "incomplete", "retrieved_at"}


def _canonical_skill_ids() -> set[str]:
    skills_doc = _load_json("skills.json")
    return {s["skill_id"] for s in skills_doc["skills"]}


def _parse_iso8601_utc(value: object, context: str) -> datetime:
    if not isinstance(value, str):
        raise CachedCatalogError(f"{context}: timestamp must be a string, got {type(value).__name__}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CachedCatalogError(f"{context}: not a valid ISO 8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise CachedCatalogError(f"{context}: timestamp must be timezone-aware: {value!r}")
    return parsed


def _validate_window(window: object, context: str) -> datetime:
    win = _require_dict(window, context)
    missing = _REQUIRED_WINDOW_FIELDS - win.keys()
    if missing:
        raise CachedCatalogError(f"{context}: missing fields {missing}")
    total_count = win["total_count"]
    if not isinstance(total_count, int) or isinstance(total_count, bool) or total_count < 0:
        raise CachedCatalogError(f"{context}: total_count must be a non-negative int, got {total_count!r}")
    if not isinstance(win["incomplete"], bool):
        raise CachedCatalogError(f"{context}: incomplete must be a bool")
    return _parse_iso8601_utc(win["retrieved_at"], f"{context}.retrieved_at")


def _validate_snapshot(snapshot: dict, skill_ids: set[str], filename: str) -> None:
    missing = _REQUIRED_SNAPSHOT_FIELDS - snapshot.keys()
    if missing:
        raise CachedCatalogError(f"{filename}: missing fields {missing}")

    if snapshot["skill_id"] not in skill_ids:
        raise CachedCatalogError(
            f"{filename}: unknown skill_id '{snapshot['skill_id']}' not present in cached skills.json"
        )
    if snapshot["skill_id"] != filename.removesuffix(".json"):
        raise CachedCatalogError(
            f"{filename}: skill_id '{snapshot['skill_id']}' does not match its own filename"
        )

    if snapshot["source_status"] not in _JAWAD_SOURCE_STATUSES:
        raise CachedCatalogError(
            f"{filename}: source_status must be one of {sorted(_JAWAD_SOURCE_STATUSES)}, "
            f"got {snapshot['source_status']!r}"
        )
    if snapshot["source_status"] == "live":
        # A snapshot FILE on disk is, by definition, being served as
        # cached data to any later reader (Jawad's own snapshot.py: "A
        # stored file is never live") — a stored file claiming "live" is
        # an unsupported live-data claim, not a valid state.
        raise CachedCatalogError(
            f"{filename}: a stored snapshot file must never claim source_status='live'"
        )
    if not snapshot.get("source_id"):
        raise CachedCatalogError(f"{filename}: no source_id (unverifiable provenance)")

    current_retrieved = _validate_window(snapshot["current"], f"{filename}.current")
    previous_retrieved = _validate_window(snapshot["previous"], f"{filename}.previous")
    if current_retrieved < previous_retrieved:
        raise CachedCatalogError(
            f"{filename}: current window retrieved_at ({current_retrieved}) is before "
            f"previous window retrieved_at ({previous_retrieved})"
        )

    if snapshot["prior_snapshot"] is not None:
        _validate_window(snapshot["prior_snapshot"], f"{filename}.prior_snapshot")


def load_cached_trend_snapshots() -> list[dict]:
    """Load and validate every app/data/cached/trend_snapshots/*.json
    file, returning plain validated dicts. Raises CachedCatalogError on
    any integrity problem rather than silently dropping or guessing.
    Validates against Jawad's own source_status enum only — see this
    module's docstring for why no translation happens here."""
    if not _TREND_SNAPSHOTS_DIR.is_dir():
        raise CachedCatalogError(f"{_TREND_SNAPSHOTS_DIR} does not exist")

    skill_ids = _canonical_skill_ids()
    snapshots: list[dict] = []
    for path in sorted(_TREND_SNAPSHOTS_DIR.glob("*.json")):
        snapshot = _require_dict(json.loads(path.read_text(encoding="utf-8")), path.name)
        _validate_snapshot(snapshot, skill_ids, path.name)
        snapshots.append(snapshot)

    seen_skill_ids = [s["skill_id"] for s in snapshots]
    if len(set(seen_skill_ids)) != len(seen_skill_ids):
        raise CachedCatalogError("Duplicate skill_id across cached trend_snapshots files")

    return snapshots
