"""Turn two WindowCounts (current 30d vs previous 30d) into a direction and a
contract-shaped TrendSignal. Pure functions, no I/O - easy to test offline.
"""
from __future__ import annotations

from .github_client import WindowCount

DIRECTION_THRESHOLD = 0.15  # >15% change to call it rising/falling, else stable

SOURCE_ID = "github_search_repos"
SIGNAL_TYPE = "developer_activity"  # NOT "job_demand" - see README.md


def compute_direction(previous_count: int | None, current_count: int | None) -> str:
    """rising/falling need a >15% change; anything else (including a zero or
    missing baseline) is stable or unknown - never a guessed direction."""
    if previous_count is None or current_count is None:
        return "unknown"
    if previous_count == 0:
        return "stable" if current_count == 0 else "unknown"
    change = (current_count - previous_count) / previous_count
    if change > DIRECTION_THRESHOLD:
        return "rising"
    if change < -DIRECTION_THRESHOLD:
        return "falling"
    return "stable"


def looks_truncated(window: WindowCount | None) -> bool:
    """True if GitHub itself flagged the search as incomplete (its search
    timed out before finishing) - such a count cannot be trusted."""
    return window is not None and window.incomplete


def build_trend_signal(
    skill_id: str,
    current: WindowCount | None,
    previous: WindowCount | None,
    role_ids: list[str],
    *,
    retrieved_at: str,
    prior: WindowCount | None = None,
) -> dict:
    """Build one contract TrendSignal dict (API_CONTRACT.md).

    direction is "unknown" whenever either window is missing or GitHub
    flagged either one as incomplete - a truncated count is never used to
    call rising/falling.
    """
    truncated = looks_truncated(current) or looks_truncated(previous)
    if truncated:
        direction = "unknown"
    else:
        direction = compute_direction(
            previous.total_count if previous else None,
            current.total_count if current else None,
        )

    if current is None:
        confidence_note = (
            "No current-window GitHub data available; this is a stale or "
            "unavailable signal, not a measurement."
        )
    elif truncated:
        confidence_note = (
            "GitHub reported this search as incomplete (timed out); the "
            "count cannot be trusted, so direction is reported as unknown "
            "rather than guessed."
        )
    else:
        prev_txt = f"{previous.total_count}" if previous else "unavailable"
        confidence_note = (
            f"GitHub repositories newly created and tagged '{current.topic}' "
            f"in {current.start}..{current.end}: {current.total_count} "
            f"(previous 30-day window {previous.start if previous else '?'}.."
            f"{previous.end if previous else '?'}: {prev_txt}). This is "
            "developer/tech-ecosystem activity on GitHub, NOT verified "
            "hiring demand."
        )

    return {
        "signal_id": f"{skill_id}_{SOURCE_ID}_{current.end if current else 'na'}",
        "skill_id": skill_id,
        "source_id": SOURCE_ID,
        "signal_type": SIGNAL_TYPE,
        "metric_name": "new_repositories_30d",
        "metric_value": current.total_count if current else None,
        "unit": "repositories",
        "observed_at": f"{current.end}T00:00:00Z" if current else None,
        "retrieved_at": retrieved_at,
        "direction": direction,
        "confidence_note": confidence_note,
        "role_ids": role_ids,
        # Extension beyond API_CONTRACT.md's TrendSignal (demo field); null on the first snapshot.
        "change_since_last_snapshot": change_since_last_snapshot(prior, current),
    }


def change_since_last_snapshot(prior: WindowCount | None, current: WindowCount | None) -> dict | None:
    """Old vs new 30-day count between two saved snapshots, with both dates.
    The two counts cover different (overlapping) 30-day windows, so this is a
    refresh-to-refresh delta, not the rising/falling comparison."""
    if prior is None or current is None:
        return None
    return {
        "old_count": prior.total_count,
        "old_window": f"{prior.start}..{prior.end}",
        "old_retrieved_at": prior.retrieved_at,
        "new_count": current.total_count,
        "new_window": f"{current.start}..{current.end}",
        "new_retrieved_at": current.retrieved_at,
    }
