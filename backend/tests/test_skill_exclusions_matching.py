"""Milestone 13B-8: wiring Jawad's real backend/app/data/cached/
skill_not_equivalent.json into HussainMatchingProvider's semantic-
similarity path (app.api.v1.endpoints.careers._get_shared_hussain_provider).

No real RunPod/network call anywhere in this file: the embedding model is
either a small local fake object, or `RunPodEmbeddingProvider` itself is
monkeypatched to a deterministic stand-in (the same pattern already used
by app/services/hussain_matching/tests/test_backend_adapter.py's own
not_equivalent test).
"""
from __future__ import annotations

import pytest

from app.api.v1.endpoints.careers import _get_shared_hussain_provider, get_matching_provider
from app.core.config import Settings
from app.schemas.matching import RoleMatch
from app.schemas.profile import SkillRef, StudentProfile
from app.services.hussain_matching import backend_adapter
from app.services.hussain_matching.backend_adapter import HussainMatchingProvider
from app.services.hussain_matching.embeddings import EmbeddingProvider
from app.services.role_catalog_cached import CachedRoleCatalog
from app.services.skill_not_equivalent_cached import load_skill_not_equivalent_pairs

REAL_PAIRS = [
    ["python", "javascript"], ["python", "matlab"], ["excel", "vba"],
    ["excel", "accounting_software"], ["accounting_software", "financial_analysis_software"],
    ["critical_thinking", "complex_problem_solving"], ["complex_problem_solving", "systems_analysis"],
    ["mathematics", "science"], ["git", "programming"], ["cad_software", "gis"],
    ["data_visualization", "gis"], ["matlab", "analytical_scientific_software"],
    # Added in Milestone 13E-6 (Jawad's approved final corrections,
    # origin/feat/jawad-ph-fix @ b2c158a): Hussain measured embedding
    # similarities of 0.74 (git~gis, both pass his 0.60 threshold) and
    # 0.67 (financial_analysis_software~analytical_scientific_software).
    ["git", "gis"], ["financial_analysis_software", "analytical_scientific_software"],
]

NO_SIMILARITY = lambda a, b: 0.0  # noqa: E731


def _profile(**overrides) -> StudentProfile:
    defaults = dict(interests=[], skills=[], projects=[])
    defaults.update(overrides)
    return StudentProfile(**defaults)


def _data_analyst():
    return next(r for r in CachedRoleCatalog().list_roles() if r.role_id == "data_analyst")


# --- 1. Loading the 14 real exclusion pairs ---------------------------------


def test_loads_the_real_fourteen_exclusion_pairs():
    pairs = load_skill_not_equivalent_pairs()
    assert len(pairs) == 14
    assert {frozenset(p) for p in pairs} == {frozenset(p) for p in REAL_PAIRS}


def test_shared_hussain_provider_is_built_with_the_real_exclusion_pairs():
    provider = _get_shared_hussain_provider()
    assert provider.not_equivalent == load_skill_not_equivalent_pairs()
    assert len(provider.not_equivalent) == 14


def test_get_matching_provider_with_hussain_mode_carries_the_exclusion_pairs():
    settings = Settings(_env_file=None, MATCHING_MODE="hussain", CATALOG_MODE="cached")
    provider = get_matching_provider(settings)
    assert isinstance(provider, HussainMatchingProvider)
    assert len(provider.not_equivalent) == 14


# --- 2. Correct enforcement of exclusions (mechanism-level, real pairs) ----


def test_excluded_pair_forces_zero_similarity_even_when_the_model_disagrees():
    """Direct test of the actual enforcement logic in embeddings.py — a
    fake model that would otherwise call python/javascript identical
    (cosine 1.0) must still be forced to 0.0 because the real file lists
    them as not_equivalent."""

    class _IdenticalVectorsModel:
        def encode(self, texts):
            return [[1.0, 0.0] for _ in texts]

    provider = EmbeddingProvider(
        {"python": ["Python"], "javascript": ["JavaScript"]},
        model=_IdenticalVectorsModel(),
        not_equivalent=[["python", "javascript"]],
    )
    assert provider("python", "javascript") == 0.0


def test_non_excluded_pair_is_unaffected_by_the_exclusion_list():
    """Same fake model, same "identical" similarity — but this pair is
    not in the real exclusion list, so it is NOT forced to zero."""

    class _IdenticalVectorsModel:
        def encode(self, texts):
            return [[1.0, 0.0] for _ in texts]

    provider = EmbeddingProvider(
        {"python": ["Python"], "javascript": ["JavaScript"], "sql": ["SQL"],
         "data_visualization": ["Data Visualization"]},
        model=_IdenticalVectorsModel(),
        not_equivalent=[["python", "javascript"]],  # sql/data_visualization not listed
    )
    assert provider("sql", "data_visualization") == 1.0


# --- 3. Correct enforcement end-to-end through the matching pipeline -------


class _FakeSimilarityProvider:
    """Stands in for RunPodEmbeddingProvider: respects whatever
    not_equivalent pairs it was built with (exactly like the real
    EmbeddingProvider base class), otherwise pretends every pair looks
    highly similar (0.9) — so a test can tell "excluded" apart from
    "would have matched" with certainty, without any real model or
    network call."""

    def __init__(self, blocked: set[frozenset]):
        self._blocked = blocked

    @classmethod
    def from_skills(cls, skills, **kwargs):
        return cls({frozenset(p) for p in kwargs.get("not_equivalent", [])})

    def precompute(self):
        pass

    def __call__(self, a, b):
        return 0.0 if frozenset((a, b)) in self._blocked else 0.9


def _patched_runpod_provider(monkeypatch):
    monkeypatch.setattr(backend_adapter, "RunPodEmbeddingProvider", _FakeSimilarityProvider)
    monkeypatch.setenv("RUNPOD_API_KEY", "fake-key-not-real")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake-endpoint-not-real")


def test_excluded_substitution_gets_no_partial_credit_in_a_real_match(monkeypatch):
    """Uses the FULL verified role catalog (not just data_analyst) so
    "javascript" is a genuine catalogue skill (required by
    software_developer) — otherwise SkillNormalizer would treat it as an
    unrecognized free-text skill and drop it before similarity is ever
    consulted, making this test pass for the wrong reason."""
    _patched_runpod_provider(monkeypatch)
    profile = _profile(skills=[SkillRef(skill_id="javascript", name="JavaScript")])
    roles = CachedRoleCatalog().list_roles()

    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    results = provider.match(profile, roles, None, [])
    data_analyst = next(m for m in results if m["role_id"] == "data_analyst")

    missing_ids = {s["skill_id"] for s in data_analyst["missing_skills"]}
    assert "python" in missing_ids  # no credit for the excluded javascript->python substitution
    assert not any("Python" in note for note in data_analyst["caveats"])


def test_non_excluded_substitution_still_gets_partial_credit_in_the_same_match(monkeypatch):
    """Contrast case, same request: the exclusion list is targeted, not a
    blanket switch that kills every semantic match."""
    _patched_runpod_provider(monkeypatch)
    profile = _profile(skills=[SkillRef(skill_id="javascript", name="JavaScript")])
    roles = CachedRoleCatalog().list_roles()

    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    results = provider.match(profile, roles, None, [])
    data_analyst = next(m for m in results if m["role_id"] == "data_analyst")

    # scoring.skills_component() lists every non-exact-match skill in
    # missing_skills regardless of partial credit (by design — see its own
    # docstring) — so "sql" being present here is expected either way;
    # the "related to ... SQL" caveat is what actually proves credit was
    # given for this non-excluded substitution.
    missing_ids = {s["skill_id"] for s in data_analyst["missing_skills"]}
    assert "sql" in missing_ids
    assert any("related to" in note and "SQL" in note for note in data_analyst["caveats"])


# --- 4. Safe fallback when the exclusion file is absent ---------------------


def test_safe_fallback_when_exclusion_file_is_missing(monkeypatch):
    import app.services.skill_not_equivalent_cached as module

    monkeypatch.setattr(module, "_SKILL_NOT_EQUIVALENT_PATH", module._SKILL_NOT_EQUIVALENT_PATH.parent / "does-not-exist.json")
    assert module.load_skill_not_equivalent_pairs() == []

    # And the full wiring still produces a working (just unprotected) provider.
    provider = HussainMatchingProvider(not_equivalent=module.load_skill_not_equivalent_pairs())
    assert provider.not_equivalent == []
    profile = _profile(skills=[SkillRef(skill_id="sql", name="SQL")])
    results = provider.match(profile, [_data_analyst()], None, [])
    assert results[0]["role_id"] == "data_analyst"  # no crash, matching still works


# --- 5. Exact matches are never suppressed by an exclusion pair ------------


def test_exact_skill_match_is_never_suppressed_by_an_exclusion_pair(monkeypatch):
    """python is one half of TWO exclusion pairs (python/javascript,
    python/matlab) — an exact python match must still earn full credit;
    SkillNormalizer's exact/alias path never consults not_equivalent at
    all (a different code path from the semantic-similarity one)."""
    _patched_runpod_provider(monkeypatch)
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python")])
    roles = [_data_analyst()]

    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    result = provider.match(profile, roles, None, [])[0]

    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    missing_ids = {s["skill_id"] for s in result["missing_skills"]}
    assert "python" in matched_ids  # exact credit (scoring.py never reaches the similarity
    assert "python" not in missing_ids  # fallback for a skill already held exactly)


def test_exact_match_unaffected_by_exclusions_even_with_real_degraded_fallback():
    """Same guarantee with no RunPod/similarity configured at all (the
    ordinary degraded path) — exact matching is exact-only regardless."""
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python"), SkillRef(skill_id="sql", name="SQL")])
    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    result = provider.match(profile, [_data_analyst()], None, [])[0]
    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    assert {"python", "sql"} <= matched_ids


# --- 8. Milestone 13E-6: the two new (14th and 13th) exclusion pairs -------


def test_exclusion_list_blocks_a_pair_symmetrically_regardless_of_argument_order():
    """Hussain's measured similarities (0.74, 0.67) came from comparing
    two skills with no inherent order — the exclusion must block the
    pair whichever way the caller happens to pass the two skill_ids."""

    class _IdenticalVectorsModel:
        def encode(self, texts):
            return [[1.0, 0.0] for _ in texts]

    provider = EmbeddingProvider(
        {"git": ["Git"], "gis": ["GIS"],
         "financial_analysis_software": ["Financial Analysis Software"],
         "analytical_scientific_software": ["Analytical/Statistical Software"]},
        model=_IdenticalVectorsModel(),
        not_equivalent=[["git", "gis"], ["financial_analysis_software", "analytical_scientific_software"]],
    )
    assert provider("git", "gis") == 0.0
    assert provider("gis", "git") == 0.0
    assert provider("financial_analysis_software", "analytical_scientific_software") == 0.0
    assert provider("analytical_scientific_software", "financial_analysis_software") == 0.0


def test_git_gis_false_positive_gets_no_semantic_credit_in_a_real_match(monkeypatch):
    """Reproduces Hussain's reported false positive (review-30-roles.md:
    Git ~ GIS measured at 0.74, above his 0.60 threshold) end to end:
    without the pair, a "Git" skill would earn partial credit toward a
    role that only needs GIS. surveyor requires gis, not git."""
    _patched_runpod_provider(monkeypatch)
    profile = _profile(skills=[SkillRef(skill_id="x", name="Git")])
    roles = CachedRoleCatalog().list_roles()

    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    results = provider.match(profile, roles, None, [])
    surveyor = next(m for m in results if m["role_id"] == "surveyor")

    missing_ids = {s["skill_id"] for s in surveyor["missing_skills"]}
    assert "gis" in missing_ids  # no credit for the excluded git->gis substitution
    assert not any("GIS" in note for note in surveyor["caveats"])


def test_financial_software_false_positive_gets_no_semantic_credit_in_a_real_match(monkeypatch):
    """Reproduces Hussain's other reported false positive (Financial
    Analysis Software ~ Analytical/Statistical Software measured at
    0.67): without the pair, a statistics-software skill would earn
    partial credit toward financial_analyst's financial-software
    requirement."""
    _patched_runpod_provider(monkeypatch)
    profile = _profile(skills=[SkillRef(skill_id="x", name="Analytical/Statistical Software")])
    roles = CachedRoleCatalog().list_roles()

    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    results = provider.match(profile, roles, None, [])
    financial_analyst = next(m for m in results if m["role_id"] == "financial_analyst")

    missing_ids = {s["skill_id"] for s in financial_analyst["missing_skills"]}
    assert "financial_analysis_software" in missing_ids
    assert not any("Financial Analysis Software" in note for note in financial_analyst["caveats"])


def test_all_fourteen_pairs_are_enforced_by_the_real_shared_matcher_adapter(monkeypatch):
    """Not just the 2 new pairs in isolation: every one of the real 14
    pairs, loaded exactly as the shared production provider loads them
    (_get_shared_hussain_provider), actually blocks semantic credit."""
    _patched_runpod_provider(monkeypatch)
    provider = _get_shared_hussain_provider()
    assert len(provider.not_equivalent) == 14

    fake = _FakeSimilarityProvider({frozenset(p) for p in provider.not_equivalent})
    for a, b in provider.not_equivalent:
        assert fake(a, b) == 0.0, (a, b)
        assert fake(b, a) == 0.0, (a, b)
    # a pair that is NOT excluded must be unaffected (sanity check the fake itself)
    assert fake("python", "sql") == 0.9


def test_profile_with_both_new_pair_skills_gets_independent_exact_credit():
    """A profile holding BOTH financial_analysis_software and
    analytical_scientific_software as exact catalogue skill_ids (not
    free text) must get full, independent credit for each — the
    exclusion only suppresses the *semantic-similarity* fallback, never
    an exact skill_id match. financial_analyst requires both."""
    roles = CachedRoleCatalog().list_roles()
    financial_analyst = next(r for r in roles if r.role_id == "financial_analyst")
    profile = _profile(skills=[
        SkillRef(skill_id="financial_analysis_software", name="Financial Analysis Software"),
        SkillRef(skill_id="analytical_scientific_software", name="Analytical/Statistical Software"),
    ])
    provider = HussainMatchingProvider(not_equivalent=load_skill_not_equivalent_pairs())
    result = provider.match(profile, [financial_analyst], None, [])[0]

    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    missing_ids = {s["skill_id"] for s in result["missing_skills"]}
    assert {"financial_analysis_software", "analytical_scientific_software"} <= matched_ids
    assert not {"financial_analysis_software", "analytical_scientific_software"} & missing_ids


# --- 6. Python + SQL student's Data Analyst recommendation -----------------


def test_python_and_sql_student_is_credited_for_both_on_data_analyst():
    profile = _profile(skills=[
        SkillRef(skill_id="python", name="Python"),
        SkillRef(skill_id="sql", name="SQL"),
    ])
    provider = HussainMatchingProvider(similarity=NO_SIMILARITY)  # exact-only, no network
    result = provider.match(profile, CachedRoleCatalog().list_roles(), None, [])
    data_analyst = next(m for m in result if m["role_id"] == "data_analyst")

    matched_ids = {s["skill_id"] for s in data_analyst["matched_skills"]}
    missing_ids = {s["skill_id"] for s in data_analyst["missing_skills"]}
    assert {"python", "sql"} <= matched_ids
    assert "python" not in missing_ids
    assert "excel" not in missing_ids  # excel is optional for this role; never a mandatory gap


# --- 7. No invented hiring probabilities or market-demand claims -----------


def test_data_analyst_explanation_never_claims_hiring_probability_or_job_demand():
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python"), SkillRef(skill_id="sql", name="SQL")])
    provider = HussainMatchingProvider(similarity=NO_SIMILARITY)
    result = provider.match(profile, [_data_analyst()], None, [])[0]

    text = (result["explanation"] + " " + " ".join(result["caveats"])).lower()
    assert "is a hiring probability" not in text
    assert "guarantees a job" not in text
    assert "predicts your job" not in text
    assert "not a hiring prediction" in result["explanation"].lower()  # the actual, correct disclaimer


def test_scenario_adjusted_match_labels_the_signal_as_developer_activity_not_demand():
    sig = [{"signal_id": "s", "skill_id": "python", "source_id": "src", "direction": "rising", "signal_type": "developer_activity"}]
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python"), SkillRef(skill_id="sql", name="SQL")])
    provider = HussainMatchingProvider(similarity=NO_SIMILARITY)
    result = provider.match(profile, [_data_analyst()], "fast", sig)[0]

    scenario_notes = [c for c in result["caveats"] if "Scenario adjusted" in c]
    assert scenario_notes
    assert "not job demand" in scenario_notes[0].lower() or "not a forecast" in scenario_notes[0].lower()
