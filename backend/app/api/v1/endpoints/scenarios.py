"""POST /scenarios/simulate — the only scenario route in the contract.

Reuses careers.py's default matching-provider/catalog/trend-provider
factories (so an override of one affects both routes consistently) and adds
one new, independently overridable dependency: get_scenario_assumptions.
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
from app.core.time import utc_now_iso
from app.db.session import get_db
from app.schemas.scenarios import ScenarioRequest, ScenarioResponse
from app.services.interfaces import MatchingProvider, TrendProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.role_catalog import RoleCatalogProvider
from app.services.scenario_service import (
    FixtureScenarioAssumptions,
    ScenarioAssumptionProvider,
    ScenarioService,
)

router = APIRouter()


def get_scenario_assumptions() -> ScenarioAssumptionProvider:
    return FixtureScenarioAssumptions()


def get_scenario_service(
    db: Session = Depends(get_db),
    matcher: MatchingProvider = Depends(get_matching_provider),
    catalog: RoleCatalogProvider = Depends(get_role_catalog),
    trends: TrendProvider = Depends(get_trend_provider),
    assumptions: ScenarioAssumptionProvider = Depends(get_scenario_assumptions),
    settings: Settings = Depends(get_settings),
) -> ScenarioService:
    matching_service = MatchingService(
        profile_service=ProfileService(db),
        catalog=catalog,
        matcher=matcher,
        trends=trends,
        matching_mode_warning=matching_mode_warning(settings),
    )
    return ScenarioService(matching_service, assumptions)


@router.post("/scenarios/simulate", response_model=ScenarioResponse)
def simulate_scenario(
    payload: ScenarioRequest,
    service: ScenarioService = Depends(get_scenario_service),
    settings: Settings = Depends(get_settings),
) -> ScenarioResponse:
    outcome = service.simulate(payload)

    return ScenarioResponse(
        data=outcome.payload,
        data_mode=catalog_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings + catalog_provenance_warnings(settings),
    )
