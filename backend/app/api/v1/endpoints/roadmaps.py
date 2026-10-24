"""POST /roadmaps/generate — the only roadmap route in the contract.

Reuses careers.py's default matching-provider/catalog/trend-provider
factories (so an override of one affects every route consistently) and
adds one new, independently overridable dependency: get_resource_catalog.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.careers import (
    catalog_data_mode,
    catalog_provenance_warnings,
    get_matching_provider,
    get_role_catalog,
    get_trend_provider,
    matching_mode_warning,
)
from app.core.config import Settings, get_settings
from app.core.integration_errors import provider_unavailable
from app.core.time import utc_now_iso
from app.db.session import get_db
from app.schemas.roadmaps import RoadmapResponse, RoleProfileRequest
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.resource_catalog import FixtureResourceCatalog, ResourceCatalogProvider
from app.services.resource_catalog_cached import CachedResourceCatalog
from app.services.roadmap_service import RoadmapService
from app.services.role_catalog import RoleCatalogProvider
from app.services.role_catalog_cached import CachedCatalogError

router = APIRouter()


def resource_provenance_warnings(settings: Settings) -> list[str]:
    """Separate from careers.py's catalog_provenance_warnings(): that one
    only speaks to role/skill/score provenance (always accurate for
    careers/scenarios). Roadmap *resource content* (title, url, hours) is
    genuinely cached real data when CATALOG_MODE=cached — this says so
    explicitly rather than letting the shared, more conservative message
    imply resources are still placeholders once they aren't."""
    if settings.CATALOG_MODE != "cached":
        return []
    return [
        "CATALOG_MODE=cached: the learning resources in this roadmap come "
        "from Jawad's verified, cached resource dataset — real course "
        "titles, URLs and provider-stated or team-estimated hours, not "
        "fixture placeholders. Which skills are selected for this roadmap "
        "is still driven by the matching score above."
    ]


def get_resource_catalog(settings: Settings = Depends(get_settings)) -> ResourceCatalogProvider:
    if settings.CATALOG_MODE == "cached":
        catalog = CachedResourceCatalog()
        try:
            catalog.list_resources()  # validate now; never silently fall back to fixture
        except CachedCatalogError as exc:
            raise provider_unavailable("ResourceCatalogProvider (cached)", str(exc)) from exc
        return catalog

    # CATALOG_MODE=fixture: the only resource catalog here is Fixture's —
    # ENABLE_FIXTURES=False must still fail closed, exactly as before.
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "ResourceCatalogProvider",
            "ENABLE_FIXTURES is false and CATALOG_MODE is 'fixture'; no "
            "non-fixture resource catalog is selected. Set CATALOG_MODE="
            "cached to use real cached resources, or leave ENABLE_FIXTURES=true.",
        )
    return FixtureResourceCatalog()


def get_roadmap_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    resources: ResourceCatalogProvider = Depends(get_resource_catalog),
    settings: Settings = Depends(get_settings),
) -> RoadmapService:
    matching_service = MatchingService(
        profile_service=ProfileService(db),
        catalog=catalog,
        matcher=matcher,
        trends=trends,
        matching_mode_warning=matching_mode_warning(settings),
    )
    return RoadmapService(matching_service, catalog, resources)


@router.post("/roadmaps/generate", response_model=RoadmapResponse)
def generate_roadmap(
    payload: RoleProfileRequest,
    service: RoadmapService = Depends(get_roadmap_service),
    settings: Settings = Depends(get_settings),
) -> RoadmapResponse:
    outcome = service.generate(payload)

    return RoadmapResponse(
        data=outcome.payload,
        data_mode=catalog_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings + catalog_provenance_warnings(settings) + resource_provenance_warnings(settings),
    )
