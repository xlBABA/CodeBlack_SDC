"""TrendProvider implementations. Both satisfy the same loosely-typed
app.services.interfaces.TrendProvider shape (latest(role_id=None)), with
different concrete return values for their two call sites:

- NullTrendProvider: used inside MatchingService (POST /careers/match).
  Unchanged from Milestone 3 — matching never considers trend signals yet,
  and this file preserves that behavior exactly.
- FixtureTrendProvider: used by GET /trends. No real trend pipeline exists
  (Jawad's services/trends/**), so this returns a small, clearly-labeled
  set of synthetic demonstration signals — never presented as sourced
  statistics or live job-market facts. `last_successful_refresh_at` is
  always None (no real source has ever been synced), and `source_status`
  is "stale" when demo signals are returned, "unavailable" when a role_id
  filter matches none of them — never "ok", since nothing is live.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.schemas.trends import SourceStatus, TrendSignal


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
