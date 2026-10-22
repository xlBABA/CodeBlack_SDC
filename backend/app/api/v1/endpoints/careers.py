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
from app.schemas.matching import MatchRequest, MatchResponse, RoleMatch
from app.schemas.profile import DataMode
from app.services.hussain_matching.backend_adapter import HussainMatchingProvider
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.role_catalog import FixtureRoleCatalog, RoleCatalogProvider
from app.services.role_catalog_cached import CachedCatalogError, CachedRoleCatalog
from app.services.trend_provider import NullTrendProvider

router = APIRouter()

# Explicit no-similarity configuration (Milestone 6C-2B, Step 4): passing
# a concrete similarity function means HussainMatchingProvider's
# _semantic_similarity() returns it immediately and never calls
# runpod_configured() at all — so no environment variable (even a
# RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID accidentally present in production)
# can activate RunPod or a local sentence-transformers model from this
# wiring. Never rely on their mere absence instead of this override.
_NO_SIMILARITY = lambda skill_a, skill_b: 0.0  # noqa: E731


def matching_mode_warning(settings: Settings) -> str | None:
    """Passed into MatchingService so its warnings stay accurate. None
    preserves MatchingService's own default fixture-mode text (still
    correct for MATCHING_MODE=fixture)."""
    if settings.MATCHING_MODE != "hussain":
        return None
    return (
        "MATCHING_MODE=hussain: scores are produced by Hussain's "
        "deterministic matching algorithm (app/services/hussain_matching), "
        "running fully offline — semantic similarity is explicitly "
        "disabled, so no RunPod endpoint or embedding model was "
        "contacted. This methodology is an initial team choice, not a "
        "validated model, and the score is not a hiring probability."
    )


def get_matching_provider(settings: Settings = Depends(get_settings)) -> MatchingProvider:
    if settings.MATCHING_MODE == "hussain":
        # Hussain's provider itself needs no fixture data, but the roles
        # it would score do if CATALOG_MODE=fixture (the default) — that
        # IS fixture catalog data. ENABLE_FIXTURES=False must not let
        # that leak through silently; only CATALOG_MODE=cached makes this
        # combination genuinely fixture-free. Fail closed otherwise.
        if not settings.ENABLE_FIXTURES and settings.CATALOG_MODE != "cached":
            raise provider_unavailable(
                "MatchingProvider (hussain)",
                "ENABLE_FIXTURES is false and CATALOG_MODE is 'fixture'; "
                "Hussain's matcher would still depend on fixture role "
                "data. Set CATALOG_MODE=cached to use real cached role "
                "data, or leave ENABLE_FIXTURES=true.",
            )
        return HussainMatchingProvider(result_model=RoleMatch, similarity=_NO_SIMILARITY)

    # ENABLE_FIXTURES=False signals "I expect real inference." No real
    # MatchingProvider implementation exists yet (Hussain's), so that case
    # must fail loudly rather than silently returning fixture scores
    # dressed up as something else. Independent of CATALOG_MODE below —
    # one gates the scoring provider, the other the role/skill data.
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "MatchingProvider",
            "ENABLE_FIXTURES is false and no real matching provider is implemented yet.",
        )
    return FixtureMatchingProvider()


def get_role_catalog(settings: Settings = Depends(get_settings)) -> RoleCatalogProvider:
    if settings.CATALOG_MODE == "cached":
        catalog = CachedRoleCatalog()
        try:
            catalog.list_roles()  # validate now; never silently fall back to fixture on failure
        except CachedCatalogError as exc:
            raise provider_unavailable("RoleCatalogProvider (cached)", str(exc)) from exc
        return catalog
    return FixtureRoleCatalog()


def catalog_data_mode(settings: Settings) -> DataMode:
    """The envelope's data_mode for every route that depends on
    get_role_catalog(). Always "fixture" for every CATALOG_MODE/
    MATCHING_MODE combination supported today: even when CATALOG_MODE=
    cached supplies real, cached O*NET-derived role/skill identifiers,
    and even when MATCHING_MODE=hussain runs a real (if still unvalidated
    and "initial team choice") algorithm instead of the fixture one, the
    actual response content these routes return — match scores and score
    breakdowns, roadmap resources (FixtureResourceCatalog) and
    recommended/simulated projects (FixtureProjectCatalog) — is still
    either fixture-generated or an unvalidated heuristic. A single
    data_mode value can't mark a response "partly cached, partly
    fixture"; labelling the whole response "cached" would let that
    content masquerade as a cached/verified outcome
    (REHAN_BACKEND_INTEGRATION.md: "don't let dummy scores accidentally
    masquerade as real outcomes"). The cached role/skill provenance and
    the active matching algorithm are both disclosed explicitly via
    catalog_provenance_warnings()/matching_mode_warning() instead of via
    this enum value.
    """
    return "fixture"


def catalog_provenance_warnings(settings: Settings) -> list[str]:
    if settings.CATALOG_MODE != "cached":
        return []
    scoring_description = (
        "Hussain's deterministic matching algorithm, running fully offline (no RunPod contacted)"
        if settings.MATCHING_MODE == "hussain"
        else "an illustrative fixture algorithm (FixtureMatchingProvider)"
    )
    return [
        "CATALOG_MODE=cached: the role and skill catalog inputs for this "
        "response come from Jawad's cached, real O*NET-derived dataset — "
        "those role/skill identifiers are not fictional. Matching scores "
        f"are still calculated by {scoring_description}, and any "
        "placeholder projects/resources/roadmap steps in this response are "
        "not verified real-world recommendations. data_mode remains "
        "'fixture' because the generated output — scores, roadmap "
        "resources, project recommendations — is still fixture-based, "
        "even though the underlying sourced roles themselves are real."
    ]


def get_trend_provider() -> TrendProvider:
    return NullTrendProvider()


def get_matching_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    settings: Settings = Depends(get_settings),
) -> MatchingService:
    return MatchingService(
        profile_service=ProfileService(db),
        catalog=catalog,
        matcher=matcher,
        trends=trends,
        matching_mode_warning=matching_mode_warning(settings),
    )


@router.post("/careers/match", response_model=MatchResponse)
def match_careers(
    payload: MatchRequest,
    service: MatchingService = Depends(get_matching_service),
    settings: Settings = Depends(get_settings),
) -> MatchResponse:
    outcome = service.match(payload)

    return MatchResponse(
        data=outcome.payload,
        data_mode=catalog_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings + catalog_provenance_warnings(settings),
    )
