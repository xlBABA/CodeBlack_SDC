"""Milestone 10C: wires Jawad's cached trend signals (app.services.jawad_trends,
vendored verbatim from feat/jawad-video-links @ 72e7ebc) into the
MatchingService call site (app.api.v1.endpoints.careers.get_trend_provider),
satisfying app.services.interfaces.TrendProvider's .latest() contract used
there — a bare list of signal dicts (NOT the TrendResult-shaped object
FixtureTrendProvider returns for GET /trends; that is a different call
site with a different actual expected shape — see interfaces.py's own
docstring).

Pure read of saved snapshot files (app/data/cached/trend_snapshots/, via
get_trends()'s base_dir parameter) — never a live GitHub API call,
in tests or in production. get_trends() computes direction/signal_type/
source_id itself (services/trends/aggregate.py); nothing here invents or
adjusts any value — only ROLES_PATH is reassigned below (a published,
intentionally-overridable module attribute, not an edit to his code) so
role_ids resolve against our actual data/roles.json location instead of
his repo-root-relative default.
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.services import jawad_trends
from app.services.jawad_trends import ingest as jawad_ingest

logger = logging.getLogger(__name__)

_TREND_SNAPSHOTS_DIR = Path(__file__).resolve().parent.parent / "data" / "cached" / "trend_snapshots"

# jawad_ingest.ROLES_PATH is only used to populate each signal's role_ids
# field (display/filtering for GET /trends) — the matching/scenario logic
# this provider feeds (services/matching/scenarios.py) filters by
# skill_id and direction only, never by role_ids, so this is cosmetic
# correctness, not load-bearing for scoring. Reassigning a module-level
# Path constant after import; never hand-edits jawad_trends/ingest.py.
_ROLES_PATH = Path(__file__).resolve().parent.parent / "data" / "cached" / "roles.json"
if _ROLES_PATH.is_file():
    jawad_ingest.ROLES_PATH = _ROLES_PATH


class CachedTrendSignalProvider:
    """Satisfies app.services.interfaces.TrendProvider for the
    MatchingService call site: .latest(role_id=None) returns a bare
    list[dict] of signals, never raising — any unreadable/malformed
    cached snapshot degrades to "no signals" (logged), never a 500."""

    def __init__(self, base_dir: Path = _TREND_SNAPSHOTS_DIR) -> None:
        self._base_dir = base_dir

    def latest(self, role_id: str | None = None) -> list[dict]:
        try:
            result = jawad_ingest.get_trends(role_id=role_id, base_dir=self._base_dir)
        except Exception as exc:  # missing/invalid/corrupt snapshot data must never 500 the request
            logger.warning(
                "Cached trend signals unavailable (%s): %s", type(exc).__name__, exc
            )
            return []
        return result.get("signals") or []


__all__ = ["CachedTrendSignalProvider"]
