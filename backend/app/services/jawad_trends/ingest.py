"""Orchestrates one trend refresh: for every covered skill, get a current vs
previous 30-day GitHub repo-creation count (fetching, or falling back to the
last saved snapshot), save the new snapshot, and build a TrendSignal.

Matches the /trends response shape (contracts/API_CONTRACT.md):
{signals: [TrendSignal], last_successful_refresh_at, source_status}.

GitHub is never retried into looking "live" when it isn't: a failed fetch
falls back to the last saved snapshot with source_status "cached", or
"unavailable" if there is no snapshot yet.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .aggregate import build_trend_signal
from .github_client import GitHubFetchError, GitHubTrendClient, WindowCount
from .queries import COVERED_SKILLS
from .snapshot import DEFAULT_SNAPSHOT_DIR, load_prior_snapshot, load_snapshot, save_snapshot

WINDOW_DAYS = 30
ROLES_PATH = Path(__file__).resolve().parents[2] / "data" / "roles.json"


def _windows_for(today: date) -> tuple[tuple[str, str], tuple[str, str]]:
    """Two non-overlapping 30-day windows ending today, as YYYY-MM-DD strings:
    ((current_start, current_end), (previous_start, previous_end))."""
    current_end = today
    current_start = current_end - timedelta(days=WINDOW_DAYS - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=WINDOW_DAYS - 1)
    fmt = "%Y-%m-%d"
    return (
        (current_start.strftime(fmt), current_end.strftime(fmt)),
        (previous_start.strftime(fmt), previous_end.strftime(fmt)),
    )


def _role_ids_by_skill() -> dict[str, list[str]]:
    """skill_id -> role_ids that require it, read fresh from data/roles.json."""
    if not ROLES_PATH.exists():
        return {}
    roles = json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for role in roles:
        for req in role.get("required_skills", []):
            out.setdefault(req["skill_id"], []).append(role["role_id"])
    return out


def refresh_skill(
    skill_id: str,
    topic: str,
    client: GitHubTrendClient,
    *,
    role_ids: list[str],
    base_dir: Path = DEFAULT_SNAPSHOT_DIR,
    today: date | None = None,
) -> tuple[dict, str]:
    """Returns (TrendSignal, source_status). source_status is "live" (fetched
    just now), "cached" (today's fetch failed, served the last snapshot), or
    "unavailable" (fetch failed and no snapshot exists yet)."""
    today = today or datetime.now(timezone.utc).date()
    (cur_start, cur_end), (prev_start, prev_end) = _windows_for(today)
    saved = load_snapshot(skill_id, base_dir)

    previous: WindowCount | None = None
    if saved and saved[1] is not None and saved[1].start == prev_start and saved[1].end == prev_end:
        previous = saved[1]  # same 30-day window already fetched today; reuse it

    current: WindowCount | None = None
    status = "live"
    try:
        if previous is None:
            previous = client.fetch_window_count(topic, prev_start, prev_end)
        current = client.fetch_window_count(topic, cur_start, cur_end)
    except GitHubFetchError:
        if saved and saved[0] is not None:
            current, previous = saved
            status = "cached"
        else:
            current, previous = None, None
            status = "unavailable"

    prior: WindowCount | None = None
    if status == "live":
        prior = saved[0] if saved else None  # read before the save overwrites it
        save_snapshot(skill_id, current, previous, base_dir)
        retrieved_at = current.retrieved_at
    elif status == "cached":
        prior = load_prior_snapshot(skill_id, base_dir)
        retrieved_at = current.retrieved_at
    else:
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    signal = build_trend_signal(
        skill_id, current, previous, role_ids, retrieved_at=retrieved_at, prior=prior
    )
    if status != "live":
        prefix = "STALE (cached snapshot): " if status == "cached" else "UNAVAILABLE: "
        signal["confidence_note"] = prefix + signal["confidence_note"]
    return signal, status


def refresh_all(
    client: GitHubTrendClient | None = None,
    *,
    base_dir: Path = DEFAULT_SNAPSHOT_DIR,
    today: date | None = None,
) -> dict:
    """Refresh every covered skill. One TrendSignal per skill per call."""
    client = client or GitHubTrendClient()
    role_ids_by_skill = _role_ids_by_skill()

    signals = []
    statuses = []
    last_live_at = None
    for skill_id, topic in COVERED_SKILLS.items():
        signal, status = refresh_skill(
            skill_id,
            topic,
            client,
            role_ids=role_ids_by_skill.get(skill_id, []),
            base_dir=base_dir,
            today=today,
        )
        signals.append(signal)
        statuses.append(status)
        if status == "live":
            last_live_at = signal["retrieved_at"]

    if all(s == "live" for s in statuses):
        overall = "live"
    elif all(s == "unavailable" for s in statuses):
        overall = "unavailable"
    else:
        overall = "cached"

    return {
        "signals": signals,
        "last_successful_refresh_at": last_live_at,
        "source_status": overall,
    }


def get_trends(
    role_id: str | None = None,
    limit: int = 20,
    *,
    base_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> dict:
    """TrendProvider.latest (contracts/API_CONTRACT.md, GET /trends).

    Pure read of the saved snapshots - no network call, so it is always
    "cached" (or "unavailable" if no snapshot exists). Use refresh_all() to
    fetch new data from GitHub.
    """
    role_ids_by_skill = _role_ids_by_skill()
    signals = []
    any_snapshot = False
    for skill_id in COVERED_SKILLS:
        saved = load_snapshot(skill_id, base_dir)
        if not saved or saved[0] is None:
            continue
        any_snapshot = True
        current, previous = saved
        role_ids = role_ids_by_skill.get(skill_id, [])
        if role_id is not None and role_id not in role_ids:
            continue
        signal = build_trend_signal(
            skill_id, current, previous, role_ids,
            retrieved_at=current.retrieved_at,
            prior=load_prior_snapshot(skill_id, base_dir),
        )
        signal["confidence_note"] = (
            f"Cached snapshot retrieved {current.retrieved_at}: " + signal["confidence_note"]
        )
        signals.append(signal)

    return {
        "signals": signals[: max(0, limit)],
        "last_successful_refresh_at": max((s["retrieved_at"] for s in signals), default=None),
        "source_status": "cached" if any_snapshot else "unavailable",
    }
