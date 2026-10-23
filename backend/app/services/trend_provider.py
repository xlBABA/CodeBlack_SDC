"""TrendProvider implementations. All satisfy the same loosely-typed
app.services.interfaces.TrendProvider shape (latest(role_id=None) ->
TrendResult), with different concrete return values for their call sites:

- NullTrendProvider: used inside MatchingService (POST /careers/match)
  when CATALOG_MODE=fixture. Unchanged from Milestone 3 — matching never
  considers trend signals in that mode, and this file preserves that
  behavior exactly.
- FixtureTrendProvider: used by GET /trends when CATALOG_MODE=fixture
  (the default). No real trend pipeline is used in this mode, so this
  returns a small, clearly-labeled set of synthetic demonstration
  signals — never presented as sourced statistics or live job-market
  facts. `last_successful_refresh_at` is always None (no real source has
  ever been synced), and `source_status` is "stale" when demo signals are
  returned, "unavailable" when a role_id filter matches none of them —
  never "ok", since nothing is live.
- CachedGithubTrendProvider (Milestone 12A): used by GET /trends when
  CATALOG_MODE=cached. Wraps the *exact same* read path as
  app.services.trend_signal_provider.CachedTrendSignalProvider (the
  provider already wired into MatchingService/scenarios for
  CATALOG_MODE=cached) — jawad_trends.ingest.get_trends(), a pure read of
  app/data/cached/trend_snapshots/*.json, never a live GitHub call — so
  GET /trends shows the identical 12 real, dated, cached GitHub
  developer-activity signals that matching/scenarios already use, instead
  of fixture demo data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.trends import SourceStatus, TrendSignal

logger = logging.getLogger(__name__)


class NullTrendProvider:
    def latest(self, role_id: str | None = None) -> list[Any]:
        return []


@dataclass
class TrendResult:
    signals: list[TrendSignal]
    last_successful_refresh_at: datetime | None
    source_status: SourceStatus


_DEMO_SIGNALS: tuple[TrendSignal, ...] = (
    TrendSignal(
        signal_id="signal_demo_001",
        skill_id="python",
        source_id="source_signal_demo_001",
        signal_type="repository_activity",
        metric_name="illustrative_demo_metric",
        observed_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        direction="rising",
        confidence_note=(
            "Synthetic/hypothetical demonstration signal; not a real sourced "
            "observation or vacancy-demand claim."
        ),
        role_ids=["data_analyst"],
    ),
    TrendSignal(
        signal_id="signal_demo_002",
        skill_id="financial_modeling",
        source_id="source_signal_demo_002",
        signal_type="repository_activity",
        metric_name="illustrative_demo_metric",
        observed_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        direction="stable",
        confidence_note=(
            "Synthetic/hypothetical demonstration signal; not a real sourced "
            "observation or vacancy-demand claim."
        ),
        role_ids=["financial_analyst"],
    ),
    TrendSignal(
        signal_id="signal_demo_003",
        skill_id="cad",
        source_id="source_signal_demo_003",
        signal_type="repository_activity",
        metric_name="illustrative_demo_metric",
        observed_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        retrieved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        direction="unknown",
        confidence_note=(
            "Synthetic/hypothetical demonstration signal; not a real sourced "
            "observation or vacancy-demand claim."
        ),
        role_ids=["mechanical_design_engineer"],
    ),
)


class FixtureTrendProvider:
    """Satisfies app.services.interfaces.TrendProvider for GET /trends."""

    def latest(self, role_id: str | None = None) -> TrendResult:
        if role_id is None:
            matched = list(_DEMO_SIGNALS)
        else:
            matched = [s for s in _DEMO_SIGNALS if role_id in s.role_ids]

        return TrendResult(
            signals=matched,
            last_successful_refresh_at=None,
            source_status="stale" if matched else "unavailable",
        )


# Jawad's jawad_trends.ingest.get_trends() reports its own source_status as
# "cached" (a snapshot was read) or "unavailable" (no snapshot exists) — it
# never returns "live" from this pure-read path (see ingest.py's get_trends
# docstring). Translated 1:1 to the public contract's ok|stale|unavailable
# enum (requirement 7): "cached" -> "stale" (real but not fresh-this-request
# data), "unavailable" -> "unavailable" unchanged. Anything else unexpected
# is mapped conservatively to "unavailable" rather than guessed as "ok".
_CACHED_INGEST_STATUS_TO_CONTRACT: dict[str, SourceStatus] = {
    "cached": "stale",
    "unavailable": "unavailable",
}

# Only these keys are ever read off a raw cached-signal dict to build a
# TrendSignal — e.g. aggregate.py's extra "change_since_last_snapshot" key
# is deliberately dropped, never passed through to the public schema.
_TREND_SIGNAL_FIELDS = frozenset(TrendSignal.model_fields)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _signal_from_cached_dict(raw: dict) -> TrendSignal | None:
    """One raw cached-signal dict (jawad_trends.aggregate.build_trend_signal's
    shape) -> a validated TrendSignal, or None if it fails validation (e.g. a
    future change to that shape drops a field this schema requires) — never
    raises past this point, and never lets a malformed signal silently
    masquerade as a real one further downstream (requirement 9)."""
    try:
        filtered = {k: v for k, v in raw.items() if k in _TREND_SIGNAL_FIELDS}
        return TrendSignal.model_validate(filtered)
    except Exception as exc:  # noqa: BLE001 - any validation failure, never a 500
        logger.warning(
            "Skipping a cached trend signal that failed schema validation (%s)",
            type(exc).__name__,
        )
        return None


class CachedGithubTrendProvider:
    """Satisfies app.services.interfaces.TrendProvider for GET /trends when
    CATALOG_MODE=cached (Milestone 12A). Reuses the identical read path as
    app.services.trend_signal_provider.CachedTrendSignalProvider (the
    MatchingService/scenarios call site) — jawad_trends.ingest.get_trends(),
    a pure read of app/data/cached/trend_snapshots/*.json, never a live
    GitHub call — so GET /trends shows the same 12 real, dated, cached
    GitHub developer-activity signals already driving matching/scenario
    adjustments, not fixture demo data.

    Never raises: a missing snapshot directory, corrupt JSON, or any other
    read/parse failure degrades to an honest empty TrendResult
    (source_status="unavailable") rather than returning misleading fixture
    signals (requirement 9) — the same fail-safe contract
    CachedTrendSignalProvider already has for its own call site.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        # Imported lazily (module-level, not at class-definition time) so
        # importing this module alone still triggers
        # trend_signal_provider's top-level ROLES_PATH-patch side effect
        # (it points jawad_trends.ingest.ROLES_PATH at our actual
        # app/data/cached/roles.json instead of its own repo-root-relative
        # default) before get_trends() ever reads role_ids for a signal.
        from app.services.trend_signal_provider import _TREND_SNAPSHOTS_DIR

        self._base_dir = base_dir or _TREND_SNAPSHOTS_DIR

    def latest(self, role_id: str | None = None) -> TrendResult:
        from app.services.jawad_trends import ingest as jawad_ingest

        try:
            result = jawad_ingest.get_trends(role_id=role_id, base_dir=self._base_dir)
        except Exception as exc:  # noqa: BLE001 - missing/corrupt snapshot data must never 500
            logger.warning(
                "Cached trend signals unavailable for GET /trends (%s): %s",
                type(exc).__name__, exc,
            )
            return TrendResult(signals=[], last_successful_refresh_at=None, source_status="unavailable")

        raw_signals = result.get("signals") or []
        signals = [s for raw in raw_signals if (s := _signal_from_cached_dict(raw)) is not None]
        raw_status = result.get("source_status", "unavailable")
        source_status = _CACHED_INGEST_STATUS_TO_CONTRACT.get(raw_status, "unavailable")
        if not signals:
            source_status = "unavailable"

        return TrendResult(
            signals=signals,
            last_successful_refresh_at=_parse_iso(result.get("last_successful_refresh_at")),
            source_status=source_status,
        )
