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
from app.services.roadmap_service import RoadmapService
from app.services.role_catalog import RoleCatalogProvider

router = APIRouter()


def get_resource_catalog(settings: Settings = Depends(get_settings)) -> ResourceCatalogProvider:
    # No non-fixture resource catalog exists at all (unlike roles, which
    # CATALOG_MODE can point at real cached data) — this dependency is
    # always fixture-sourced. ENABLE_FIXTURES=False must fail closed here
    # regardless of MATCHING_MODE/CATALOG_MODE, per Milestone 6C-2B Step
    # 3: a real matching algorithm must not silently unlock fixture
    # roadmap resources it doesn't actually make real.
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "ResourceCatalogProvider",
            "ENABLE_FIXTURES is false; no non-fixture resource catalog exists yet.",
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
        warnings=outcome.warnings + catalog_provenance_warnings(settings),
    )
