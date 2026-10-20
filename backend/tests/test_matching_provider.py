from app.schemas.profile import SkillRef, StudentProfile
from app.services.matching_provider import FixtureMatchingProvider
from app.services.role_catalog import FixtureRoleCatalog, RoleFixture, RoleRequirement

CATALOG = FixtureRoleCatalog().list_roles()
DATA_ANALYST = next(r for r in CATALOG if r.role_id == "data_analyst")


def _profile(**overrides) -> StudentProfile:
    defaults = dict(interests=[], skills=[], projects=[])
    defaults.update(overrides)
    return StudentProfile(**defaults)


def test_full_skill_match_scores_100_skills_and_no_missing():
    profile = _profile(
        skills=[SkillRef(skill_id=req.skill_id, name=req.name) for req in DATA_ANALYST.required_skills]
    )
    result = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]

    assert result.score_breakdown.skills == 100.0
    assert result.missing_skills == []
    assert {s.skill_id for s in result.matched_skills} == {
        req.skill_id for req in DATA_ANALYST.required_skills
    }


def test_no_skill_match_scores_0_skills_and_all_missing():
    profile = _profile(skills=[SkillRef(skill_id="unrelated", name="Unrelated")])
    result = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]

    assert result.score_breakdown.skills == 0.0
    assert len(result.missing_skills) == len(DATA_ANALYST.required_skills)
    assert result.matched_skills == []


def test_matching_is_deterministic_for_same_input():
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    first = FixtureMatchingProvider().match(profile, CATALOG, "moderate", [])
    second = FixtureMatchingProvider().match(profile, CATALOG, "moderate", [])

    assert [m.model_dump() for m in first] == [m.model_dump() for m in second]


def test_ranking_is_descending_by_score():
    profile = _profile(
        skills=[SkillRef(skill_id=req.skill_id, name=req.name) for req in DATA_ANALYST.required_skills]
    )
    results = FixtureMatchingProvider().match(profile, CATALOG, None, [])

    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_tie_break_is_deterministic_by_role_id():
    tied_requirement = (RoleRequirement("x", "X", weight=1.0),)
    role_b = RoleFixture(
        role_id="role_b",
        role_title="Role B",
        category="Test",
        min_semester=1,
        required_skills=tied_requirement,
        transferable_interests=(),
        evidence_ids=(),
    )
    role_a = RoleFixture(
        role_id="role_a",
        role_title="Role A",
        category="Test",
        min_semester=1,
        required_skills=tied_requirement,
        transferable_interests=(),
        evidence_ids=(),
    )
    profile = _profile(skills=[SkillRef(skill_id="x", name="X")])

    results = FixtureMatchingProvider().match(profile, [role_b, role_a], None, [])

    assert [r.role_id for r in results] == ["role_a", "role_b"]


def test_score_breakdown_values_within_0_100():
    profile = _profile()
    results = FixtureMatchingProvider().match(profile, CATALOG, None, [])
    for match in results:
        for value in (
            match.score,
            match.score_breakdown.skills,
            match.score_breakdown.experience,
            match.score_breakdown.prerequisites,
            match.score_breakdown.transferable,
        ):
            assert 0.0 <= value <= 100.0


def test_caveats_disclaim_hiring_prediction_and_fixture_status():
    profile = _profile()
    result = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]

    joined = " ".join(result.caveats).lower()
    assert "fixture" in joined
    assert "hiring" in joined


def test_scenario_id_adds_caveat_without_changing_score():
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    without_scenario = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]
    with_scenario = FixtureMatchingProvider().match(profile, [DATA_ANALYST], "fast", [])[0]

    assert without_scenario.score == with_scenario.score
    assert len(with_scenario.caveats) == len(without_scenario.caveats) + 1
