from sqlalchemy import inspect

from app.core.errors import AppError
from app.db.models import StudentProfileORM
from app.fixtures.sample_profiles import SAMPLE_PROFILES
from app.services.profile_service import ProfileService, to_schema


def test_schema_initialization(test_engine):
    table_names = inspect(test_engine).get_table_names()
    assert "student_profiles" in table_names
    assert "student_profile_skills" in table_names


def test_session_is_isolated_and_empty(db_session):
    assert db_session.query(StudentProfileORM).count() == 0


def test_create_and_retrieve_profile(db_session):
    service = ProfileService(db_session)
    sample = SAMPLE_PROFILES["cs_undergrad_data"]

    created, was_created = service.upsert(sample)
    assert was_created is True
    assert created.profile_id.startswith("profile_")

    fetched = service.get(created.profile_id)
    assert fetched is not None
    schema = to_schema(fetched)
    assert schema.degree == "Computer Science"
    assert {s.skill_id for s in schema.skills} == {"sql", "python"}


def test_lookup_unknown_profile_returns_none(db_session):
    service = ProfileService(db_session)
    assert service.get("profile_does_not_exist") is None


def test_update_existing_profile_replaces_skills(db_session):
    service = ProfileService(db_session)
    sample = SAMPLE_PROFILES["cs_undergrad_data"]

    created, _ = service.upsert(sample)
    profile_id = created.profile_id

    updated_payload = sample.model_copy(
        update={
            "profile_id": profile_id,
            "skills": [sample.skills[0]],  # drop "python"
            "degree": "Information Systems",
        }
    )
    updated, was_created = service.upsert(updated_payload)

    assert was_created is False
    assert updated.profile_id == profile_id
    schema = to_schema(updated)
    assert schema.degree == "Information Systems"
    assert [s.skill_id for s in schema.skills] == ["sql"]


def test_upsert_with_unknown_supplied_profile_id_raises_not_found(db_session):
    service = ProfileService(db_session)
    sample = SAMPLE_PROFILES["cs_undergrad_data"].model_copy(
        update={"profile_id": "profile_unknown_123"}
    )

    try:
        service.upsert(sample)
        assert False, "expected AppError"
    except AppError as exc:
        assert exc.code == "PROFILE_NOT_FOUND"
        assert exc.status_code == 404


def test_multiple_profiles_do_not_cross_contaminate(db_session):
    service = ProfileService(db_session)
    first, _ = service.upsert(SAMPLE_PROFILES["cs_undergrad_data"])
    second, _ = service.upsert(SAMPLE_PROFILES["business_finance_student"])

    assert first.profile_id != second.profile_id

    first_schema = to_schema(service.get(first.profile_id))
    second_schema = to_schema(service.get(second.profile_id))

    assert first_schema.degree == "Computer Science"
    assert second_schema.degree == "Business Administration"
    assert {s.skill_id for s in first_schema.skills}.isdisjoint(
        {s.skill_id for s in second_schema.skills}
    )
