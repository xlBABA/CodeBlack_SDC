"""POST /projects/recommend and POST /projects/simulate — the only project
routes in the contract.

Reuses careers.py's default matching-provider/catalog/trend-provider
factories and adds one new, independently overridable dependency:
get_project_catalog.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.careers import get_matching_provider, get_role_catalog, get_trend_provider
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


def get_project_catalog() -> ProjectCatalogProvider:
    return FixtureProjectCatalog()


def _matching_service(
    db: Session, matcher: MatchingProvider, catalog: RoleCatalogProvider, trends: TrendProvider
) -> MatchingService:
    return MatchingService(
        profile_service=ProfileService(db), catalog=catalog, matcher=matcher, trends=trends
    )


def get_project_recommendation_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    projects: ProjectCatalogProvider = Depends(get_project_catalog),
) -> ProjectRecommendationService:
    return ProjectRecommendationService(_matching_service(db, matcher, catalog, trends), projects)


def get_project_simulation_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    projects: ProjectCatalogProvider = Depends(get_project_catalog),
) -> ProjectSimulationService:
    return ProjectSimulationService(_matching_service(db, matcher, catalog, trends), projects)


@router.post("/projects/recommend", response_model=ProjectRecommendationResponse)
def recommend_projects(
    payload: RoleProfileRequest,
    service: ProjectRecommendationService = Depends(get_project_recommendation_service),
) -> ProjectRecommendationResponse:
    outcome = service.recommend(payload)

    return ProjectRecommendationResponse(
        data=ProjectRecommendationPayload(projects=outcome.projects),
        data_mode="fixture",
        generated_at=utc_now_iso(),
        warnings=outcome.warnings,
    )


@router.post("/projects/simulate", response_model=ProjectSimulationResponse)
def simulate_project(
    payload: ProjectSimulationRequest,
    service: ProjectSimulationService = Depends(get_project_simulation_service),
) -> ProjectSimulationResponse:
    outcome = service.simulate(payload)

    return ProjectSimulationResponse(
        data=outcome.payload,
        data_mode="fixture",
        generated_at=utc_now_iso(),
        warnings=outcome.warnings,
    )
