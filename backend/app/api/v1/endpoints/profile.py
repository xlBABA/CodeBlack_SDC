"""POST /profile/analyze — the only profile route in contracts/API_CONTRACT.md.

The contract defines no separate GET/PUT profile endpoints, so this single
route infers create-vs-update from whether `profile_id` is supplied and
known (see ProfileService.upsert). Lookup/update behavior is exercised
directly at the service layer in tests, not via new public routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.time import utc_now_iso
from app.db.session import get_db
from app.schemas.profile import ProfileResponse, StudentProfile
from app.services.profile_service import ProfileService, to_schema

router = APIRouter()


@router.post("/profile/analyze", response_model=ProfileResponse)
def analyze_profile(payload: StudentProfile, db: Session = Depends(get_db)) -> ProfileResponse:
    service = ProfileService(db)
    model, _created = service.upsert(payload)

    return ProfileResponse(
        data=to_schema(model),
        data_mode="live",
        generated_at=utc_now_iso(),
        warnings=[],
    )
