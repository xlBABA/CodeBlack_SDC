"""POST /roadmaps/generate — the only roadmap route in the contract.

Reuses careers.py's default matching-provider/catalog/trend-provider
factories (so an override of one affects every route consistently) and
adds one new, independently overridable dependency: get_resource_catalog.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.careers import get_matching_provider, get_role_catalog, get_trend_provider
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


def get_resource_catalog() -> ResourceCatalogProvider:
    return FixtureResourceCatalog()


def get_roadmap_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    resources: ResourceCatalogProvider = Depends(get_resource_catalog),
) -> RoadmapService:
    matching_service = MatchingService(
        profile_service=ProfileService(db),
        catalog=catalog,
        matcher=matcher,
        trends=trends,
    )
    return RoadmapService(matching_service, catalog, resources)


@router.post("/roadmaps/generate", response_model=RoadmapResponse)
def generate_roadmap(
    payload: RoleProfileRequest,
    service: RoadmapService = Depends(get_roadmap_service),
) -> RoadmapResponse:
    outcome = service.generate(payload)

    return RoadmapResponse(
        data=outcome.payload,
        data_mode="fixture",
        generated_at=utc_now_iso(),
        warnings=outcome.warnings,
    )
