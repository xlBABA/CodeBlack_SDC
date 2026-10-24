from app.schemas.profile import SkillRef, StudentProfile
from app.services.matching_provider import FixtureMatchingProvider
from app.services.role_catalog import FixtureRoleCatalog, RoleFixture, RoleRequirement
from app.services.role_catalog_cached import load_cached_roles

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


def test_caveats_disclaim_hiring_prediction_and_illustrative_status():
    """Milestone (Jawad fix, 2026-10-25): the caveat text used to say
    "Fixture role catalog ... pending Jawad's verified 30-role dataset
    and Hussain's real scoring model" — internal jargon, a teammate's
    name, and (once that dataset and model existed) factually stale. It
    must now say the same thing in student-safe, always-true terms: this
    specific provider's scoring is illustrative/unvalidated, regardless
    of which role catalog it happens to be scoring."""
    profile = _profile()
    result = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]

    joined = " ".join(result.caveats).lower()
    assert "illustrative" in joined or "unvalidated" in joined
    assert "hiring" in joined
    assert "jawad" not in joined
    assert "hussain" not in joined


def test_scenario_id_adds_caveat_without_changing_score():
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    without_scenario = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]
    with_scenario = FixtureMatchingProvider().match(profile, [DATA_ANALYST], "fast", [])[0]

    assert without_scenario.score == with_scenario.score
    assert len(with_scenario.caveats) == len(without_scenario.caveats) + 1


# --- Milestone 6B-2: min_semester=None and required/optional skills ---

_NO_PREREQ_ROLE = RoleFixture(
    role_id="cached_style_role",
    role_title="Cached-Style Role",
    category="Test",
    min_semester=None,  # e.g. Jawad's cached catalog: empty prerequisites list
    required_skills=(RoleRequirement("sql", "SQL", weight=1.0),),
    transferable_interests=(),
    evidence_ids=("onet_x",),
)


def test_min_semester_none_does_not_crash_and_scores_prerequisites_as_fully_met():
    profile = _profile(semester=3, skills=[SkillRef(skill_id="sql", name="SQL")])
    result = FixtureMatchingProvider().match(profile, [_NO_PREREQ_ROLE], None, [])[0]

    assert result.score_breakdown.prerequisites == 100.0


def test_min_semester_none_does_not_crash_even_with_unknown_profile_semester():
    profile = _profile(semester=None, skills=[SkillRef(skill_id="sql", name="SQL")])
    result = FixtureMatchingProvider().match(profile, [_NO_PREREQ_ROLE], None, [])[0]

    assert result.score_breakdown.prerequisites == 100.0


def test_existing_min_semester_prerequisite_still_scored_as_before():
    """Regression: roles with a real min_semester (every original fixture
    role) must keep their exact prior scoring — the None branch must not
    change this path at all."""
    below_requirement = _profile(semester=1)  # data_analyst requires semester 3
    at_requirement = _profile(semester=3)
    unknown_standing = _profile(semester=None)

    below_result = FixtureMatchingProvider().match(below_requirement, [DATA_ANALYST], None, [])[0]
    at_result = FixtureMatchingProvider().match(at_requirement, [DATA_ANALYST], None, [])[0]
    unknown_result = FixtureMatchingProvider().match(unknown_standing, [DATA_ANALYST], None, [])[0]

    assert below_result.score_breakdown.prerequisites == 33.0  # max(20, round(100*1/3))
    assert at_result.score_breakdown.prerequisites == 100.0
    assert unknown_result.score_breakdown.prerequisites == 50.0


_MIXED_REQUIRED_OPTIONAL_ROLE = RoleFixture(
    role_id="mixed_role",
    role_title="Mixed Role",
    category="Test",
    min_semester=1,
    required_skills=(
        RoleRequirement("sql", "SQL", weight=1.0, required=True),
        RoleRequirement("excel", "Excel", weight=0.6, required=False),
    ),
    transferable_interests=(),
    evidence_ids=("onet_x",),
)


def test_unmatched_optional_skill_is_not_presented_as_a_missing_gap():
    profile = _profile()  # matches neither sql nor excel
    result = FixtureMatchingProvider().match(profile, [_MIXED_REQUIRED_OPTIONAL_ROLE], None, [])[0]

    missing_ids = {s.skill_id for s in result.missing_skills}
    assert missing_ids == {"sql"}  # the required skill only
    assert "excel" not in missing_ids


def test_unmatched_optional_skill_is_not_silently_discarded():
    """Not shown in missing_skills, but not dropped either — surfaced via
    a caveat so it isn't lost information."""
    profile = _profile()
    result = FixtureMatchingProvider().match(profile, [_MIXED_REQUIRED_OPTIONAL_ROLE], None, [])[0]

    joined = " ".join(result.caveats)
    assert "Excel" in joined
    assert "not counted as missing-skill gaps" in joined.lower()


def test_matched_optional_skill_still_counts_toward_score_unchanged_methodology():
    """Scoring formula (weight-sum) is untouched — an optional skill the
    student DOES have still contributes its weight exactly as before."""
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL"), SkillRef(skill_id="excel", name="Excel")])
    result = FixtureMatchingProvider().match(profile, [_MIXED_REQUIRED_OPTIONAL_ROLE], None, [])[0]

    assert result.score_breakdown.skills == 100.0
    assert {s.skill_id for s in result.matched_skills} == {"sql", "excel"}
    assert result.missing_skills == []


def test_explanation_denominator_counts_only_required_skills():
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    result = FixtureMatchingProvider().match(profile, [_MIXED_REQUIRED_OPTIONAL_ROLE], None, [])[0]

    assert "1/1 required skills present" in result.explanation


def test_fixture_role_matching_unaffected_by_required_optional_split():
    """Every original fixture role has every skill implicitly required=True
    (the default) — adding the field must not change their behavior."""
    profile = _profile(skills=[SkillRef(skill_id=req.skill_id, name=req.name) for req in DATA_ANALYST.required_skills])
    result = FixtureMatchingProvider().match(profile, [DATA_ANALYST], None, [])[0]

    assert result.score_breakdown.skills == 100.0
    assert result.missing_skills == []
    assert not any("Optional" in caveat for caveat in result.caveats)


def test_fixture_matching_provider_does_not_crash_against_real_cached_roles():
    """Integration-readiness check only — CachedRoleCatalog is still not
    wired into any DI/endpoint. This loads the real cached data directly
    (same as the cached-catalog tests do) and proves Fix 2's min_semester
    handling holds against the actual data, not just a synthetic role."""
    cached_roles = load_cached_roles()
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])

    results = FixtureMatchingProvider().match(profile, cached_roles, None, [])

    assert len(results) == len(cached_roles)
    for result in results:
        assert 0.0 <= result.score_breakdown.prerequisites <= 100.0


def test_cached_roles_optional_skills_never_appear_in_missing_skills():
    """Same real-data check for Fix 1: an unmatched optional skill from
    Jawad's cached catalog (e.g. "excel" on data_analyst) must not surface
    in missing_skills. Checked per-role, since the same skill_id (e.g.
    "excel") is optional on some roles but genuinely required on others
    (financial_analyst) — a global set would wrongly flag that case."""
    cached_roles = load_cached_roles()
    profile = _profile()  # matches no skills at all
    results_by_role = {r.role_id: r for r in FixtureMatchingProvider().match(profile, cached_roles, None, [])}

    any_optional_checked = False
    for role in cached_roles:
        role_optional_ids = {req.skill_id for req in role.required_skills if not req.required}
        if not role_optional_ids:
            continue
        any_optional_checked = True
        missing_ids = {s.skill_id for s in results_by_role[role.role_id].missing_skills}
        assert not (missing_ids & role_optional_ids), (role.role_id, missing_ids, role_optional_ids)

    assert any_optional_checked, "sanity check: at least one cached role must actually have an optional skill"
