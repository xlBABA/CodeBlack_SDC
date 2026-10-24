"""GET /sdgs/{role_id} — the only SDG route in the contract.

Stateless: no profile/DB dependency. Unlike careers/roadmaps/projects,
this route has no scoring/heuristic layer riding on top of its catalog —
the entire response content comes directly from whichever SDG catalog is
selected, so data_mode can accurately reflect that catalog's real
provenance (no "conservative fixture always" override needed here).
"""
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.integration_errors import provider_unavailable
from app.core.time import utc_now_iso
from app.schemas.profile import DataMode
from app.schemas.sdgs import SdgResponse
from app.services.role_catalog_cached import CachedCatalogError
from app.services.sdg_catalog import FixtureSdgCatalog, SdgCatalogProvider
from app.services.sdg_catalog_cached import CachedSdgCatalog, load_cached_sdg_mappings
from app.services.sdg_service import SdgService

router = APIRouter()

_CACHED_PROVENANCE_WARNING = (
    "These role and skill links to the UN Sustainable Development Goals, "
    "and their reasons, come from our checked dataset. They are not a "
    "United Nations endorsement or official certification, and do not "
    "measure independently verified real-world impact."
)


def sdg_data_mode(settings: Settings) -> DataMode:
    return "cached" if settings.CATALOG_MODE == "cached" else "fixture"


def sdg_provenance_warning(settings: Settings) -> str | None:
    """None preserves SdgService's own default fixture-mode disclaimer
    text (still correct for CATALOG_MODE=fixture)."""
    if settings.CATALOG_MODE != "cached":
        return None
    return _CACHED_PROVENANCE_WARNING


def get_sdg_catalog(settings: Settings = Depends(get_settings)) -> SdgCatalogProvider:
    if settings.CATALOG_MODE == "cached":
        try:
            load_cached_sdg_mappings()  # validate now; never silently fall back to fixture
        except CachedCatalogError as exc:
            raise provider_unavailable("SdgCatalogProvider (cached)", str(exc)) from exc
        return CachedSdgCatalog()

    # CATALOG_MODE=fixture: the only SDG catalog here is Fixture's —
    # ENABLE_FIXTURES=False must fail closed here too (new as of
    # Milestone 6D-2D — this route was previously never gated at all).
    if not settings.ENABLE_FIXTURES:
        raise provider_unavailable(
            "SdgCatalogProvider",
            "ENABLE_FIXTURES is false and CATALOG_MODE is 'fixture'; no "
            "non-fixture SDG catalog is selected. Set CATALOG_MODE=cached "
            "to use real cached SDG mappings, or leave ENABLE_FIXTURES=true.",
        )
    return FixtureSdgCatalog()


def get_sdg_service(
    catalog: SdgCatalogProvider = Depends(get_sdg_catalog),
    settings: Settings = Depends(get_settings),
) -> SdgService:
    return SdgService(catalog, provenance_warning=sdg_provenance_warning(settings))


@router.get("/sdgs/{role_id}", response_model=SdgResponse)
def get_sdgs(
    role_id: str,
    service: SdgService = Depends(get_sdg_service),
    settings: Settings = Depends(get_settings),
) -> SdgResponse:
    outcome = service.get_mappings(role_id)

    return SdgResponse(
        data=outcome.payload,
        data_mode=sdg_data_mode(settings),
        generated_at=utc_now_iso(),
        warnings=outcome.warnings,
    )
