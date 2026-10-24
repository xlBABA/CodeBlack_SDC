"""Milestone 13C-7: integration coverage for Hussain's latest reviewed
matcher fixes (origin/feature/hussain-matching @ 54b0906), ported
verbatim into app/services/hussain_matching/{normalizer,matcher,
backend_adapter}.py, plus the skills_coverage propagation this backend
needed to add on its own (RoleFixture -> role_catalog_cached.py ->
role_to_matcher_format -> Matcher) for his caveat to ever reach a real
response.

No real RunPod call anywhere in this file.
"""
from __future__ import annotations

import pytest

from app.schemas.profile import SkillRef, StudentProfile
from app.services.hussain_matching.backend_adapter import HussainMatchingProvider
from app.services.hussain_matching.matcher import LIMITED_COVERAGE_CAVEAT, NO_SKILLS_CAVEAT
from app.services.role_catalog_cached import CachedCatalogError, CachedRoleCatalog, load_cached_roles

NO_SIMILARITY = lambda a, b: 0.0  # noqa: E731

# Confirmed against the real, current app/data/cached/roles.json —
# re-verify this set if Jawad's data changes the flagged roles again.
# public_health_analyst joined this set in Milestone 13D-9 (Jawad's approved
# "Option C" rebuild, origin/feat/jawad-ph-fix @ 1cf9b74): it was flagged
# limited coverage because our 20-skill catalog cannot represent its
# epidemiology-specific Knowledge/software (Biology, Medicine and Dentistry,
# CDC Epi Info, SaTScan), not because of a catalog defect.
REAL_LIMITED_COVERAGE_ROLE_IDS = {
    "financial_analyst", "information_security_analyst",
    "financial_risk_specialist", "logistician", "public_health_analyst",
}


def _profile(**overrides) -> StudentProfile:
    defaults = dict(interests=[], skills=[], projects=[])
    defaults.update(overrides)
    return StudentProfile(**defaults)


# --- 1. skills_coverage propagates through the real loader -----------------


def test_skills_coverage_propagates_from_real_roles_json_through_role_fixture():
    roles = load_cached_roles()
    flagged = {r.role_id for r in roles if r.skills_coverage == "limited"}
    assert flagged == REAL_LIMITED_COVERAGE_ROLE_IDS
    unflagged_sample = next(r for r in roles if r.role_id == "data_analyst")
    assert unflagged_sample.skills_coverage is None


def test_skills_coverage_value_is_validated_not_silently_ignored(monkeypatch):
    """A typo'd value (e.g. "Limited") must fail loudly, not silently do
    nothing once the matcher starts reading it."""
    import app.services.role_catalog_cached as module

    real_load_json = module._load_json
    raw_roles = real_load_json("roles.json")
    bad_roles = [dict(r) for r in raw_roles]
    bad_roles[0]["skills_coverage"] = "Limited"  # wrong case

    def _fake_load_json(name):
        return bad_roles if name == "roles.json" else real_load_json(name)

    monkeypatch.setattr(module, "_load_json", _fake_load_json)
    with pytest.raises(CachedCatalogError, match="skills_coverage must be 'limited' or absent"):
        module.load_cached_roles()


# --- 2. Real limited-coverage roles get the caveat end-to-end --------------


def test_real_limited_coverage_roles_carry_the_caveat_through_matching():
    roles = CachedRoleCatalog().list_roles()
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])

    by_id = {m["role_id"]: m for m in results}
    for role_id in REAL_LIMITED_COVERAGE_ROLE_IDS:
        assert LIMITED_COVERAGE_CAVEAT in by_id[role_id]["caveats"], role_id
    # A representative unflagged role must never get it.
    assert LIMITED_COVERAGE_CAVEAT not in by_id["data_analyst"]["caveats"]


def test_real_limited_coverage_roles_end_to_end_via_careers_match_api(client, monkeypatch):
    from app.api.v1.endpoints.careers import get_settings
    from app.core.config import Settings
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, CATALOG_MODE="cached", MATCHING_MODE="hussain", ENABLE_FIXTURES=False
    )
    try:
        # MatchRequest.limit's frozen contract maximum is 6; a profile
        # holding financial_risk_specialist's own required skills ranks
        # it (and its limited-coverage siblings sharing similar tools)
        # inside that top-6, so this still exercises the real endpoint
        # without exceeding the contract.
        response = client.post(
            "/api/v1/careers/match",
            json={
                "profile": {
                    "interests": [], "projects": [],
                    "skills": [
                        {"skill_id": sid, "name": sid}
                        for sid in ("attention_to_detail", "excel", "financial_analysis_software",
                                    "sql", "analytical_scientific_software", "python", "vba",
                                    "data_visualization")
                    ],
                },
                "limit": 6,
            },
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 200
    matches = response.json()["data"]["matches"]
    by_id = {m["role_id"]: m for m in matches}
    limited_in_response = REAL_LIMITED_COVERAGE_ROLE_IDS & by_id.keys()
    assert limited_in_response  # the profile is designed to surface at least one
    for role_id in limited_in_response:
        assert LIMITED_COVERAGE_CAVEAT in by_id[role_id]["caveats"], role_id


# --- 3. Empty-skill-profile caveat on every match, via the real API -------


def test_empty_skills_profile_shows_no_recognised_skills_caveat_via_api(client):
    from app.api.v1.endpoints.careers import get_settings
    from app.core.config import Settings
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, CATALOG_MODE="cached", MATCHING_MODE="hussain", ENABLE_FIXTURES=False
    )
    try:
        response = client.post(
            "/api/v1/careers/match", json={"profile": {"interests": [], "skills": [], "projects": []}, "limit": 6}
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 200
    matches = response.json()["data"]["matches"]
    assert matches and all(NO_SKILLS_CAVEAT in m["caveats"] for m in matches)


# --- 4. Generic "Accounting" never silently maps to accounting_software ---


def test_generic_accounting_gets_no_credit_against_the_real_catalog():
    """"Accounting" must never be silently credited toward
    accounting_software: it stays an unmet, missing required skill, and
    the "Did you mean" suggestion is surfaced (as a top-level warning,
    not a per-match caveat — see Matcher.match_roles' own warnings list)."""
    roles = CachedRoleCatalog().list_roles()
    accountant = next(r for r in roles if r.role_id == "accountant")
    profile = {"interests": [], "projects": [], "skills": [{"name": "Accounting"}]}

    from app.services.hussain_matching.matcher import Matcher
    from app.services.hussain_matching.normalizer import SkillNormalizer
    from app.services.hussain_matching.backend_adapter import catalogue_from_roles, role_to_matcher_format
    from app.services.role_catalog_cached import _load_json

    role_dict = role_to_matcher_format(accountant)
    catalogue = catalogue_from_roles([accountant], _load_json("skills.json")["skills"])
    data = Matcher(SkillNormalizer(catalogue), NO_SIMILARITY).match_roles(profile, [role_dict], None, [], limit=1)
    result = data["matches"][0]

    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    missing_ids = {s["skill_id"] for s in result["missing_skills"]}
    assert "accounting_software" not in matched_ids
    assert "accounting_software" in missing_ids
    assert any("Did you mean Accounting Software?" in w for w in data["warnings"])


def test_generic_accounting_is_rejected_even_when_a_fake_model_would_score_it_high():
    """The structural guarantee: the fragment-of-a-longer-name rule runs
    BEFORE the embedding step, so a real, reachable, highly-confident
    RunPod score can never override it — the interpreter is never even
    called."""
    from app.services.hussain_matching.normalizer import SkillNormalizer
    from app.services.role_catalog_cached import _load_json

    normalizer = SkillNormalizer(_load_json("skills.json")["skills"])
    asked = []

    def eager_interpreter(names):
        asked.extend(names)
        return [("accounting_software", 0.82)] * len(names)

    resolved, warnings, interpreted = normalizer.interpret_profile_skills(
        [{"name": "Accounting"}], eager_interpreter
    )
    assert resolved == {} and interpreted == {}
    assert asked == []  # never offered to the model at all
    assert any("Did you mean Accounting Software?" in w for w in warnings)


def test_legitimate_accounting_software_aliases_still_match_exactly():
    from app.services.hussain_matching.normalizer import SkillNormalizer
    from app.services.role_catalog_cached import _load_json

    normalizer = SkillNormalizer(_load_json("skills.json")["skills"])
    for alias in ("QuickBooks", "Intuit QuickBooks", "GnuCash", "Accounting Software"):
        result = normalizer.normalize(alias)
        assert result.skill_id == "accounting_software", alias


# --- 5. "Python (pandas)" resolves with a visible confirmation caveat -----


def test_python_pandas_resolves_with_partial_credit_and_confirm_caveat():
    """Unlike an embedding-interpreted DIFFERENT skill (which only gives
    the role's actual required skill partial credit indirectly, while
    that skill itself stays "missing" — see Milestone 13B-8/13B-9),
    "Python (pandas)" is interpreted as python ITSELF: the interpretation
    folds "python" into the held-skills dict directly, so it is reported
    as matched (with RELATED_CREDIT applied, not full), not missing —
    the caveat is what actually discloses the partial/unconfirmed credit."""
    roles = CachedRoleCatalog().list_roles()
    data_analyst = next(r for r in roles if r.role_id == "data_analyst")
    profile = _profile(skills=[SkillRef(skill_id="x", name="Python (pandas)")])

    result = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, [data_analyst], None, [])[0]
    assert any(
        'Interpreted "Python (pandas)" as Python (it contains "Python")' in c and "please confirm" in c
        for c in result["caveats"]
    )
    assert "python" in {s["skill_id"] for s in result["matched_skills"]}
    assert "python" not in {s["skill_id"] for s in result["missing_skills"]}


# --- 6. Exact matches and exclusions are unaffected -------------------------


def test_exact_skill_matches_still_work_after_the_normalizer_changes():
    roles = CachedRoleCatalog().list_roles()
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python"), SkillRef(skill_id="sql", name="SQL")])
    result = next(
        m for m in HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])
        if m["role_id"] == "data_analyst"
    )
    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    assert {"python", "sql"} <= matched_ids


def test_not_equivalent_exclusions_still_present_and_unaffected():
    from app.services.skill_not_equivalent_cached import load_skill_not_equivalent_pairs

    pairs = load_skill_not_equivalent_pairs()
    assert len(pairs) == 12


# --- 7. No accidental change to weights/ranking for unrelated roles --------


def test_scores_for_roles_untouched_by_the_fix_are_bit_for_bit_identical():
    """The normalizer/matcher changes only affect free-text interpretation
    and two new caveats — exact-skill-id scoring math for an ordinary
    profile must be byte-for-byte unchanged. Regression-proof by
    recomputing the exact scores this milestone's own report cites from
    Milestone 13C-4 (Python+SQL profile, data_analyst) and asserting they
    still match."""
    roles = CachedRoleCatalog().list_roles()
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python"), SkillRef(skill_id="sql", name="SQL")])
    result = next(
        m for m in HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])
        if m["role_id"] == "data_analyst"
    )
    assert result["score"] == 12  # unchanged from Milestone 13C-4's measurement
    assert result["score_breakdown"]["skills"] == 17
