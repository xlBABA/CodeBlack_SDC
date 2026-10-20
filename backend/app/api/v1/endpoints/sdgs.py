"""GET /sdgs/{role_id} — the only SDG route in the contract.

Stateless: no profile/DB dependency.
"""
from fastapi import APIRouter, Depends

from app.core.time import utc_now_iso
from app.schemas.sdgs import SdgResponse
from app.services.sdg_catalog import FixtureSdgCatalog, SdgCatalogProvider
from app.services.sdg_service import SdgService

router = APIRouter()


def get_sdg_catalog() -> SdgCatalogProvider:
    return FixtureSdgCatalog()


def get_sdg_service(catalog: SdgCatalogProvider = Depends(get_sdg_catalog)) -> SdgService:
    return SdgService(catalog)


@router.get("/sdgs/{role_id}", response_model=SdgResponse)
def get_sdgs(role_id: str, service: SdgService = Depends(get_sdg_service)) -> SdgResponse:
    outcome = service.get_mappings(role_id)

    return SdgResponse(
        data=outcome.payload,
        data_mode="fixture",
        generated_at=utc_now_iso(),
        warnings=outcome.warnings,
    )
