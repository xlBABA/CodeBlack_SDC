"""POST /careers/match — the only matching route implemented in this
milestone. GET /careers/{role_id} is in the contract but out of scope here:
it needs Jawad's real role-detail/SDG/evidence data, which doesn't exist
yet, and is deferred to a future milestone rather than stubbed.

Each provider is its own Depends() so tests (or a future real integration)
can override just one — e.g. swap only get_matching_provider for Hussain's
real matcher without touching the DB or catalog wiring.

get_matching_provider is also imported by scenarios.py, roadmaps.py and
projects.py, so the ENABLE_FIXTURES gate below applies consistently to
every route that scores a role, from this one change.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.integration_errors import provider_unavailable
from app.core.time import utc_now_iso
from app.db.session import get_db
from app.schemas.matching import MatchRequest, MatchResponse
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.role_catalog import FixtureRoleCatalog, RoleCatalogProvider
from app.services.trend_provider import NullTrendProvider

router = APIRouter()


def get_matching_provider(settings: Settings = Depends(get_settings)) -> MatchingProvider:
    # ENABLE_FIXTURES=False signals "I expect real inference." No real
    # MatchingProvider implementation exists yet (Hussain's), so that case
    # must fail loudly rather than silently returning fixture scores
    # dressed up as something else.
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "MatchingProvider",
            "ENABLE_FIXTURES is false and no real matching provider is implemented yet.",
        )
    return FixtureMatchingProvider()


def get_role_catalog() -> RoleCatalogProvider:
    return FixtureRoleCatalog()


def get_trend_provider() -> TrendProvider:
    return NullTrendProvider()


def get_matching_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
) -> MatchingService:
    return MatchingService(
        profile_service=ProfileService(db),
        catalog=catalog,
        matcher=matcher,
        trends=trends,
    )


@router.post("/careers/match", response_model=MatchResponse)
def match_careers(
    payload: MatchRequest,
    service: MatchingService = Depends(get_matching_service),
) -> MatchResponse:
    outcome = service.match(payload)

    return MatchResponse(
        data=outcome.payload,
        data_mode="fixture",
        generated_at=utc_now_iso(),
        warnings=outcome.warnings,
    )
