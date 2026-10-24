"""GET /trends — the only trend retrieval route in contracts/API_CONTRACT.md.

Stateless: no profile/DB dependency.

Milestone 12A: CATALOG_MODE=cached now makes this route return the same 12
real, dated, cached GitHub developer-activity signals (app/data/cached/
trend_snapshots/) that already drive MatchingService/scenario calculations
via app.services.trend_signal_provider.CachedTrendSignalProvider — fixing
the discrepancy where matching used real cached signals but this route
still showed fixture demo data. CATALOG_MODE=fixture (the default) is
unchanged: still the small, clearly-labeled synthetic demonstration set.
"""
from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.core.time import utc_now_iso
from app.schemas.profile import DataMode
from app.schemas.trends import TrendsPayload, TrendsResponse
from app.services.interfaces import TrendProvider
from app.services.trend_provider import CachedGithubTrendProvider, FixtureTrendProvider

router = APIRouter()

_FIXTURE_WARNING = (
    "No real trend source is connected yet; any signals shown are "
    "synthetic, clearly-labeled hypothetical placeholders demonstrating "
    "the contract shape, not sourced evidence or live job-market data."
)
_CACHED_WARNING = (
    "CATALOG_MODE=cached: these are Jawad's real, dated, cached GitHub "
    "developer-activity signals (app/data/cached/trend_snapshots) — "
    "GitHub repository creation/activity volume, NOT verified hiring "
    "demand or job vacancies. Not every skill has a covered signal; see "
    "each signal's confidence_note for its exact source and retrieval date."
)
_CACHED_NO_SIGNALS_WARNING = (
    "No cached trend signal is currently available for this request — the "
    "snapshot directory may be missing/unreadable, or no covered skill "
    "matches the given role_id. This is an honest empty result, never a "
    "fixture signal shown in its place."
)


def get_trend_provider(settings: Settings = Depends(get_settings)) -> TrendProvider:
    if settings.CATALOG_MODE == "cached":
        return CachedGithubTrendProvider()
    return FixtureTrendProvider()


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    role_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1),
    settings: Settings = Depends(get_settings),
    provider: TrendProvider = Depends(get_trend_provider),
) -> TrendsResponse:
    result = provider.latest(role_id=role_id)
    signals = result.signals[:limit]

    payload = TrendsPayload(
        signals=signals,
        last_successful_refresh_at=result.last_successful_refresh_at,
        source_status=result.source_status,
    )

    if settings.CATALOG_MODE == "cached":
        data_mode: DataMode = "cached"
        warnings = [_CACHED_WARNING]
        if not signals:
            warnings.append(_CACHED_NO_SIGNALS_WARNING)
    else:
        data_mode = "fixture"
        warnings = [_FIXTURE_WARNING]

    return TrendsResponse(
        data=payload,
        data_mode=data_mode,
        generated_at=utc_now_iso(),
        warnings=warnings,
    )
