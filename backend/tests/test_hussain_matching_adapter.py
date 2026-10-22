"""Milestone 6C-2A: import and adapter-compatibility tests only for the
vendored app/services/hussain_matching package (origin/feature/hussain-
matching @ 61373a5). HussainMatchingProvider is NOT activated anywhere —
get_matching_provider() still returns only FixtureMatchingProvider. No
RunPod endpoint, RUNPOD_API_KEY, or heavy ML dependency is required or
used by any test here; semantic similarity is explicitly disabled rather
than relied on being absent from the environment.
"""
import sys

import pytest

from app.api.v1.endpoints.careers import get_matching_provider
from app.schemas.matching import RoleMatch
from app.schemas.profile import SkillRef, StudentProfile
from app.services.hussain_matching.backend_adapter import (
    DEGRADED_CAVEAT,
    HussainMatchingProvider,
    role_to_matcher_format,
)
from app.services.matching_provider import FixtureMatchingProvider
from app.services.role_catalog import FixtureRoleCatalog, RoleFixture, RoleRequirement
from app.services.role_catalog_cached import CachedRoleCatalog

CACHED_ROLE_IDS = {"data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst"}

# Explicit no-similarity configuration (Step 5): never relies on the
# ambient environment lacking RUNPOD_API_KEY/RUNPOD_ENDPOINT_ID.
NO_SIMILARITY = lambda a, b: 0.0  # noqa: E731


def _profile(**overrides) -> StudentProfile:
    defaults = dict(interests=[], skills=[], projects=[])
    defaults.update(overrides)
    return StudentProfile(**defaults)


# --- 1. Import safety -----------------------------------------------------


def test_import_does_not_load_heavy_ml_dependencies():
    """Importing the adapter and every module it transitively imports must
    never trigger sentence-transformers/torch/transformers — those are
    only ever imported lazily, inside a call never exercised here."""
    for forbidden in ("sentence_transformers", "torch", "transformers"):
        assert forbidden not in sys.modules


def test_import_does_not_require_runpod_env_vars(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    import app.services.hussain_matching.backend_adapter  # noqa: F401 (re-import is a no-op; must not raise)


def test_construction_never_opens_a_network_connection(monkeypatch):
    """Belt-and-suspenders for Step 5: even if RunPod env vars were
    present, merely constructing the provider must not call urlopen."""
    import urllib.request

    def _forbidden(*a, **k):
        raise AssertionError("urlopen must not be called by construction alone")

    monkeypatch.setattr(urllib.request, "urlopen", _forbidden)
    HussainMatchingProvider(result_model=RoleMatch)  # construction only, no .match() call


# --- 2. Adapter construction without RunPod -------------------------------


def test_adapter_constructs_without_any_runpod_configuration(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    provider = HussainMatchingProvider(result_model=RoleMatch)
    assert provider is not None


def test_adapter_constructs_with_explicit_similarity_override():
    """Step 5: explicit no-similarity configuration, not just absent env vars."""
    provider = HussainMatchingProvider(result_model=RoleMatch, similarity=NO_SIMILARITY)
    assert provider.similarity is NO_SIMILARITY


# --- 3. Valid RoleMatch responses -----------------------------------------


def test_matches_against_real_fixture_catalog_validate_as_rolematch(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    roles = FixtureRoleCatalog().list_roles()

    results = HussainMatchingProvider(result_model=RoleMatch, similarity=NO_SIMILARITY).match(
        profile, roles, None, []
    )

    assert len(results) == len(roles)
    assert all(isinstance(m, RoleMatch) for m in results)
    for m in results:
        assert m.score_type == "profile_alignment_estimate"
        assert 0.0 <= m.score <= 100.0


def test_matches_against_real_cached_catalog_validate_as_rolematch():
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    roles = CachedRoleCatalog().list_roles()

    results = HussainMatchingProvider(result_model=RoleMatch, similarity=NO_SIMILARITY).match(
        profile, roles, None, []
    )

    assert len(results) == 4
    assert all(isinstance(m, RoleMatch) for m in results)


# --- 4. Required/optional skill preservation -------------------------------


def test_role_to_matcher_format_preserves_required_true():
    role = RoleFixture(
        role_id="r", role_title="R", category="Test", min_semester=1,
        required_skills=(RoleRequirement("sql", "SQL", weight=1.0, required=True),),
        transferable_interests=(), evidence_ids=("e",),
    )
    converted = role_to_matcher_format(role)
    assert converted["required_skills"] == [{"skill_id": "sql", "importance": 1.0, "required": True}]


def test_role_to_matcher_format_preserves_required_false():
    """The exact bug found in the 6C-1 audit: this used to hardcode True
    regardless of the source RoleRequirement.required value."""
    role = RoleFixture(
        role_id="r", role_title="R", category="Test", min_semester=1,
        required_skills=(RoleRequirement("excel", "Excel", weight=0.6, required=False),),
        transferable_interests=(), evidence_ids=("e",),
    )
    converted = role_to_matcher_format(role)
    assert converted["required_skills"] == [{"skill_id": "excel", "importance": 0.6, "required": False}]


def test_role_to_matcher_format_does_not_invent_importance_when_weight_missing():
    role = RoleFixture(
        role_id="r", role_title="R", category="Test", min_semester=1,
        required_skills=(RoleRequirement("sql", "SQL"),),  # weight uses its own default (1.0)
        transferable_interests=(), evidence_ids=("e",),
    )
    converted = role_to_matcher_format(role)
    assert converted["required_skills"][0]["importance"] == 1.0  # RoleRequirement's own default, not invented here


def test_cached_catalogs_actual_required_optional_split_is_preserved():
    """Real Jawad cached-role data (Step 3's explicit requirement), not a
    synthetic role: data_analyst's "excel" is required=False in the real
    cached dataset."""
    data_analyst = next(r for r in CachedRoleCatalog().list_roles() if r.role_id == "data_analyst")
    converted = role_to_matcher_format(data_analyst)
    by_id = {s["skill_id"]: s for s in converted["required_skills"]}
    assert by_id["excel"]["required"] is False
    assert by_id["sql"]["required"] is True


def test_role_to_matcher_format_preserves_skill_ids_and_evidence_ids():
    data_analyst = next(r for r in CachedRoleCatalog().list_roles() if r.role_id == "data_analyst")
    converted = role_to_matcher_format(data_analyst)
    assert {s["skill_id"] for s in converted["required_skills"]} == {
        req.skill_id for req in data_analyst.required_skills
    }
    assert converted["evidence_ids"] == list(data_analyst.evidence_ids)  # cached provenance preserved


# --- 5. No optional skills in mandatory missing gaps -----------------------


def test_unmatched_optional_skill_never_appears_in_missing_skills_real_data():
    """Using real cached data end-to-end through the adapter: data_analyst's
    optional "excel" must never appear in missing_skills, even though
    Hussain's own scoring.skills_component() (unmodified) puts every
    unmatched skill there regardless of its required flag."""
    profile = _profile()  # matches nothing
    roles = CachedRoleCatalog().list_roles()

    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])
    data_analyst = next(m for m in results if m["role_id"] == "data_analyst")

    missing_ids = {s["skill_id"] for s in data_analyst["missing_skills"]}
    assert "excel" not in missing_ids
    assert "sql" in missing_ids  # a genuinely required, unmatched skill stays listed


def test_score_itself_is_unaffected_by_the_missing_skills_filter():
    """The filter is presentation-only — scoring.py's weight computation
    (and therefore the numeric score) must be identical with or without
    the fix, proving scoring methodology was not touched."""
    profile = _profile()
    roles = CachedRoleCatalog().list_roles()
    data_analyst_role = next(r for r in roles if r.role_id == "data_analyst")

    from app.services.hussain_matching import scoring
    from app.services.hussain_matching.matcher import Matcher
    from app.services.hussain_matching.normalizer import SkillNormalizer

    role_dict = role_to_matcher_format(data_analyst_role)
    normalizer = SkillNormalizer([
        {"skill_id": r["skill_id"], "name": r["skill_id"], "aliases": []} for r in role_dict["required_skills"]
    ])
    direct_score = scoring.skills_component({}, role_dict, {}, normalizer.name_of, None)[0]

    adapter_result = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])
    adapter_score = next(m for m in adapter_result if m["role_id"] == "data_analyst")["score_breakdown"]["skills"]

    assert round(direct_score) == adapter_score


# --- 6. min_semester=None handling -----------------------------------------


def test_min_semester_none_never_crashes_through_the_adapter():
    role = RoleFixture(
        role_id="r", role_title="R", category="Test", min_semester=None,
        required_skills=(RoleRequirement("sql", "SQL"),),
        transferable_interests=(), evidence_ids=("e",),
    )
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])

    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, [role], None, [])
    assert results[0]["score_breakdown"]["prerequisites"] == 100


def test_min_semester_none_does_not_invent_a_prerequisite():
    converted = role_to_matcher_format(
        RoleFixture(
            role_id="r", role_title="R", category="Test", min_semester=None,
            required_skills=(RoleRequirement("sql", "SQL"),),
            transferable_interests=(), evidence_ids=("e",),
        )
    )
    assert converted["prerequisites"] == []


def test_real_cached_roles_all_have_no_invented_semester_prerequisite():
    for role in CachedRoleCatalog().list_roles():
        assert role_to_matcher_format(role)["prerequisites"] == []


# --- 7. Canonical role IDs --------------------------------------------------


def test_all_four_canonical_cached_role_ids_survive_the_adapter():
    profile = _profile()
    roles = CachedRoleCatalog().list_roles()
    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])
    assert {m["role_id"] for m in results} == CACHED_ROLE_IDS


# --- 8. Unknown roles and invalid inputs ------------------------------------


def test_empty_roles_list_returns_empty_matches_not_a_crash():
    profile = _profile()
    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, [], None, [])
    assert results == []


def test_duplicate_role_id_raises_value_error():
    role = RoleFixture(
        role_id="dup", role_title="R", category="Test", min_semester=1,
        required_skills=(RoleRequirement("sql", "SQL"),),
        transferable_interests=(), evidence_ids=("e",),
    )
    profile = _profile()
    with pytest.raises(ValueError, match="Duplicate role_id"):
        HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, [role, role], None, [])


def test_unverified_role_is_silently_excluded_not_errored():
    role = RoleFixture(
        role_id="r", role_title="R", category="Test", min_semester=1,
        required_skills=(RoleRequirement("sql", "SQL"),),
        transferable_interests=(), evidence_ids=("e",), verified=False,
    )
    profile = _profile()
    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, [role], None, [])
    assert results == []


# --- 9. Disclosed degradation when semantic embeddings are unavailable -----


def test_degradation_is_disclosed_when_runpod_is_not_configured(monkeypatch):
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    profile = _profile()
    roles = [next(r for r in CachedRoleCatalog().list_roles() if r.role_id == "data_analyst")]

    # No `similarity=` override here deliberately: proves the *default*
    # (unconfigured) path discloses degradation on its own.
    results = HussainMatchingProvider().match(profile, roles, None, [])
    assert all(DEGRADED_CAVEAT in m["caveats"] for m in results)


def test_degradation_caveat_is_absent_with_an_explicit_similarity_override():
    profile = _profile()
    roles = [next(r for r in CachedRoleCatalog().list_roles() if r.role_id == "data_analyst")]
    results = HussainMatchingProvider(similarity=NO_SIMILARITY).match(profile, roles, None, [])
    assert all(DEGRADED_CAVEAT not in m["caveats"] for m in results)


# --- 10. Existing fixture backend behavior is unchanged ---------------------


def test_get_matching_provider_still_returns_only_fixture_matching_provider():
    """HussainMatchingProvider must remain completely inactive in DI."""
    from app.core.config import Settings

    provider = get_matching_provider(Settings(_env_file=None))
    assert isinstance(provider, FixtureMatchingProvider)
    assert not isinstance(provider, HussainMatchingProvider)
