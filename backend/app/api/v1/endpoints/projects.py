"""POST /projects/recommend and POST /projects/simulate — the only project
routes in the contract.

Reuses careers.py's default matching-provider/catalog/trend-provider
factories and adds one new, independently overridable dependency:
get_project_catalog.
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
from app.schemas.projects import (
    ProjectRecommendationPayload,
    ProjectRecommendationResponse,
    ProjectSimulationRequest,
    ProjectSimulationResponse,
)
from app.schemas.roadmaps import RoleProfileRequest
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.project_catalog import FixtureProjectCatalog, ProjectCatalogProvider
from app.services.project_service import ProjectRecommendationService, ProjectSimulationService
from app.services.role_catalog import RoleCatalogProvider

router = APIRouter()


def get_project_catalog(settings: Settings = Depends(get_settings)) -> ProjectCatalogProvider:
    # No non-fixture project catalog exists at all — always fixture-
    # sourced, so ENABLE_FIXTURES=False fails closed here regardless of
    # MATCHING_MODE/CATALOG_MODE. See get_resource_catalog() in
    # roadmaps.py for the identical reasoning.
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "ProjectCatalogProvider",
            "ENABLE_FIXTURES is false; no non-fixture project catalog exists yet.",
        )
    return FixtureProjectCatalog()


def _matching_service(
    db: Session, matcher: MatchingProvider, catalog: RoleCatalogProvider, trends: TrendProvider,
    settings: Settings,
) -> MatchingService:
    return MatchingService(
        profile_service=ProfileService(db), catalog=catalog, matcher=matcher, trends=trends,
        matching_mode_warning=matching_mode_warning(settings),
    )


def get_project_recommendation_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    projects: ProjectCatalogProvider = Depends(get_project_catalog),
    settings: Settings = Depends(get_settings),
) -> ProjectRecommendationService:
    return ProjectRecommendationService(
        _matching_service(db, matcher, catalog, trends, settings), projects
    )


def get_project_simulation_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    projects: ProjectCatalogProvider = Depends(get_project_catalog),
    settings: Settings = Depends(get_settings),
) -> ProjectSimulationService:
    return ProjectSimulationService(
        _matching_service(db, matcher, catalog, trends, settings), projects
    )


@router.post("/projects/recommend", response_model=ProjectRecommendationResponse)
def recommend_projects(
    payload: RoleProfileRequest,
    service: ProjectRecommendationService = Depends(get_project_recommendation_service),
    settings: Settings = Depends(get_settings),
) -> ProjectRecommendationResponse:
    outcome = service.recommend(payload)

    return ProjectRecommendationResponse(
        data=ProjectRecommendationPayload(projects=outcome.projects),
        data_mode=catalog_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings + catalog_provenance_warnings(settings),
    )


@router.post("/projects/simulate", response_model=ProjectSimulationResponse)
def simulate_project(
    payload: ProjectSimulationRequest,
    service: ProjectSimulationService = Depends(get_project_simulation_service),
    settings: Settings = Depends(get_settings),
) -> ProjectSimulationResponse:
    outcome = service.simulate(payload)

    return ProjectSimulationResponse(
        data=outcome.payload,
        data_mode=catalog_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings + catalog_provenance_warnings(settings),
    )
