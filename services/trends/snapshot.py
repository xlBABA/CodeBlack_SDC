"""Persist one JSON snapshot per skill: current + previous window counts and
when we last successfully reached GitHub for that skill. This is what lets a
"refresh" fall back to real stale data (never a fake "live" number) when
GitHub is down or rate-limited.
"""
from __future__ import annotations

import json
from pathlib import Path

from .github_client import WindowCount

DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "trend_snapshots"


def snapshot_path(skill_id: str, base_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Path:
    return base_dir / f"{skill_id}.json"


def _window_to_dict(w: WindowCount | None) -> dict | None:
    if w is None:
        return None
    return {
        "topic": w.topic,
        "start": w.start,
        "end": w.end,
        "total_count": w.total_count,
        "incomplete": w.incomplete,
        "retrieved_at": w.retrieved_at,
    }


def _dict_to_window(d: dict | None) -> WindowCount | None:
    if d is None:
        return None
    return WindowCount(
        topic=d["topic"],
        start=d["start"],
        end=d["end"],
        total_count=d["total_count"],
        incomplete=d.get("incomplete", False),
        retrieved_at=d["retrieved_at"],
    )


def save_snapshot(
    skill_id: str,
    current: WindowCount | None,
    previous: WindowCount | None,
    base_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """Overwrites the skill's snapshot. The old snapshot's current window is
    kept as `prior_snapshot` so "what changed since last time" can be shown."""
    path = snapshot_path(skill_id, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    old = load_snapshot(skill_id, base_dir)
    payload = {
        "skill_id": skill_id,
        # A stored file is never live: whoever reads it later is serving cached data.
        "source_status": "cached",
        "source_id": "github_search_repos",
        "current": _window_to_dict(current),
        "previous": _window_to_dict(previous),
        "prior_snapshot": _window_to_dict(old[0]) if old else None,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_snapshot(
    skill_id: str, base_dir: Path = DEFAULT_SNAPSHOT_DIR
) -> tuple[WindowCount | None, WindowCount | None] | None:
    """Returns (current, previous) from the last saved snapshot, or None if
    no snapshot exists yet for this skill."""
    path = snapshot_path(skill_id, base_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return _dict_to_window(data.get("current")), _dict_to_window(data.get("previous"))


def load_prior_snapshot(skill_id: str, base_dir: Path = DEFAULT_SNAPSHOT_DIR) -> WindowCount | None:
    """The current window of the snapshot before the latest one, if any."""
    path = snapshot_path(skill_id, base_dir)
    if not path.exists():
        return None
    return _dict_to_window(json.loads(path.read_text(encoding="utf-8")).get("prior_snapshot"))
