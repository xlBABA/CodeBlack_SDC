import pytest

from app.core.errors import AppError
from app.schemas.matching import MatchRequest
from app.schemas.profile import SkillRef, StudentProfile
from app.services.matching_provider import FixtureMatchingProvider
from app.services.matching_service import MatchingService
from app.services.profile_service import ProfileService
from app.services.role_catalog import FixtureRoleCatalog
from app.services.trend_provider import NullTrendProvider


def _service(db_session) -> MatchingService:
    return MatchingService(
        profile_service=ProfileService(db_session),
        catalog=FixtureRoleCatalog(),
        matcher=FixtureMatchingProvider(),
        trends=NullTrendProvider(),
    )


def test_match_with_inline_profile_does_not_touch_db(db_session):
    service = _service(db_session)
    profile = StudentProfile(interests=[], skills=[SkillRef(skill_id="sql", name="SQL")], projects=[])

    outcome = service.match(MatchRequest(profile=profile))

    assert len(outcome.payload.matches) == 4  # full fixture catalog, within limit=6 default
    assert outcome.payload.catalog_coverage.verified == 4
    assert outcome.payload.catalog_coverage.total_target == 30


def test_match_with_known_profile_id_uses_stored_profile(db_session):
    profile_service = ProfileService(db_session)
    stored, _ = profile_service.upsert(
        StudentProfile(interests=[], skills=[SkillRef(skill_id="sql", name="SQL")], projects=[])
    )

    service = _service(db_session)
    # Inline payload intentionally stale/different — stored data must win.
    request_profile = StudentProfile(profile_id=stored.profile_id, interests=[], skills=[], projects=[])
    outcome = service.match(MatchRequest(profile=request_profile))

    data_analyst = next(m for m in outcome.payload.matches if m.role_id == "data_analyst")
    assert any(s.skill_id == "sql" for s in data_analyst.matched_skills)


def test_match_with_unknown_profile_id_raises_not_found(db_session):
    service = _service(db_session)
    request_profile = StudentProfile(profile_id="profile_missing", interests=[], skills=[], projects=[])

    with pytest.raises(AppError) as exc_info:
        service.match(MatchRequest(profile=request_profile))

    assert exc_info.value.code == "PROFILE_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_limit_truncates_results(db_session):
    service = _service(db_session)
    profile = StudentProfile(interests=[], skills=[], projects=[])

    outcome = service.match(MatchRequest(profile=profile, limit=1))

    assert len(outcome.payload.matches) == 1
