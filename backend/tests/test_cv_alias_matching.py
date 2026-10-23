"""Milestone 13B-9: Jawad's six approved CV skill aliases
(excel: "Advanced Excel"; sql: "Microsoft SQL Server", "MySQL",
"PostgreSQL"; cad_software: "CAD"; gis: "QGIS") now reach
HussainMatchingProvider's exact-match path through careers.py's
_get_shared_hussain_provider(), which passes the real
app/data/cached/skills.json as `skills_catalogue=` — not just the CV
extraction normalizer (app.services.cv_extraction_service), which already
read skills.json directly before this milestone.

No real RunPod/network call anywhere in this file.
"""
from __future__ import annotations

from app.api.v1.endpoints.careers import _get_shared_hussain_provider
from app.schemas.profile import SkillRef, StudentProfile
from app.services.hussain_matching import backend_adapter
from app.services.hussain_matching.backend_adapter import HussainMatchingProvider
from app.services.hussain_matching.normalizer import SkillNormalizer
from app.services.role_catalog_cached import CachedRoleCatalog, _load_json
from app.services.skill_not_equivalent_cached import load_skill_not_equivalent_pairs

NO_SIMILARITY = lambda a, b: 0.0  # noqa: E731

NEW_ALIASES = {
    "CAD": "cad_software",
    "QGIS": "gis",
    "Microsoft SQL Server": "sql",
    "MySQL": "sql",
    "PostgreSQL": "sql",
    "Advanced Excel": "excel",
}


def _real_skills_catalogue() -> list[dict]:
    return _load_json("skills.json")["skills"]


def _profile(**overrides) -> StudentProfile:
    defaults = dict(interests=[], skills=[], projects=[])
    defaults.update(overrides)
    return StudentProfile(**defaults)


# --- 1. All six aliases resolve correctly -----------------------------------


def test_all_six_new_cv_aliases_resolve_to_their_skill_id():
    normalizer = SkillNormalizer(_real_skills_catalogue())
    for alias, expected_skill_id in NEW_ALIASES.items():
        result = normalizer.normalize(alias)
        assert result.skill_id == expected_skill_id, f"{alias!r} resolved to {result.skill_id!r}"


# --- 2. Aliases work through the actual matching provider, not just the CV
#        normalizer -------------------------------------------------------


def test_aliases_resolve_through_the_real_shared_matching_provider():
    """Uses _get_shared_hussain_provider("cached") itself — the exact
    object careers.py's get_matching_provider() returns in production
    under CATALOG_MODE=cached — rather than a hand-built
    HussainMatchingProvider, to prove the real wiring (skills_catalogue=
    real skills.json) is what's under test. Only CATALOG_MODE=cached
    wires skills_catalogue at all — see careers.py's own comment on why
    CATALOG_MODE=fixture must not (a fixture-only skill_id collides with
    the real catalog's new "CAD" alias)."""
    provider = _get_shared_hussain_provider("cached")
    assert provider.skills_catalogue is not None
    assert {s["skill_id"] for s in provider.skills_catalogue} >= {"cad_software", "gis", "sql", "excel"}

    profile = _profile(skills=[
        SkillRef(skill_id="x1", name="QGIS"),
        SkillRef(skill_id="x2", name="CAD"),
        SkillRef(skill_id="x3", name="Microsoft SQL Server"),
    ])
    roles = CachedRoleCatalog().list_roles()
    civil_engineer = next(r for r in roles if r.role_id == "civil_engineer")  # requires gis + cad_software

    results = HussainMatchingProvider(
        skills_catalogue=provider.skills_catalogue, similarity=NO_SIMILARITY,
    ).match(profile, [civil_engineer], None, [])
    matched_ids = {s["skill_id"] for s in results[0]["matched_skills"]}
    assert {"gis", "cad_software"} <= matched_ids


def test_cv_normalizer_and_matching_provider_agree_on_the_same_aliases():
    """Both consumers must resolve the same alias to the same skill_id —
    the CV extraction path (app.services.cv_extraction_service, which
    already read skills.json directly) and the matching path (now wired
    the same way via careers.py)."""
    from app.services.cv_extraction_service import _load_skill_catalogue

    cv_normalizer = SkillNormalizer(_load_skill_catalogue())
    match_normalizer = SkillNormalizer(_real_skills_catalogue())
    for alias, expected_skill_id in NEW_ALIASES.items():
        assert cv_normalizer.normalize(alias).skill_id == expected_skill_id
        assert match_normalizer.normalize(alias).skill_id == expected_skill_id


# --- 3. No spurious substring matches ---------------------------------------


def test_cad_alias_does_not_spuriously_match_cadence_or_academic():
    normalizer = SkillNormalizer(_real_skills_catalogue())
    assert normalizer.normalize("cadence").skill_id is None
    assert normalizer.normalize("academic").skill_id is None
    assert normalizer.normalize("CAD").skill_id == "cad_software"  # the real alias still works


def test_qgis_alias_does_not_spuriously_match_qgismap():
    normalizer = SkillNormalizer(_real_skills_catalogue())
    assert normalizer.normalize("QGISmap").skill_id is None
    assert normalizer.normalize("QGIS Map").skill_id is None
    assert normalizer.normalize("QGIS").skill_id == "gis"  # the real alias still works


# --- 4. Exact matches remain intact ------------------------------------------


def test_exact_skill_id_matches_remain_intact_after_alias_wiring():
    profile = _profile(skills=[SkillRef(skill_id="python", name="Python"), SkillRef(skill_id="sql", name="SQL")])
    provider = HussainMatchingProvider(skills_catalogue=_real_skills_catalogue(), similarity=NO_SIMILARITY)
    roles = CachedRoleCatalog().list_roles()
    result = next(m for m in provider.match(profile, roles, None, []) if m["role_id"] == "data_analyst")
    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    assert {"python", "sql"} <= matched_ids


# --- 5. Excluded semantic substitutions remain blocked -----------------------


class _FakeSimilarityProvider:
    """Same deterministic stand-in as Milestone 13B-8's
    test_skill_exclusions_matching.py — respects not_equivalent, else
    pretends every pair looks highly similar (0.9). No network call."""

    def __init__(self, blocked: set[frozenset]):
        self._blocked = blocked

    @classmethod
    def from_skills(cls, skills, **kwargs):
        return cls({frozenset(p) for p in kwargs.get("not_equivalent", [])})

    def precompute(self):
        pass

    def __call__(self, a, b):
        return 0.0 if frozenset((a, b)) in self._blocked else 0.9


def test_excluded_substitution_still_blocked_with_skills_catalogue_wired(monkeypatch):
    monkeypatch.setattr(backend_adapter, "RunPodEmbeddingProvider", _FakeSimilarityProvider)
    monkeypatch.setenv("RUNPOD_API_KEY", "fake-key-not-real")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", "fake-endpoint-not-real")

    profile = _profile(skills=[SkillRef(skill_id="javascript", name="JavaScript")])
    roles = CachedRoleCatalog().list_roles()

    provider = HussainMatchingProvider(
        skills_catalogue=_real_skills_catalogue(),
        not_equivalent=load_skill_not_equivalent_pairs(),
    )
    results = provider.match(profile, roles, None, [])
    data_analyst = next(m for m in results if m["role_id"] == "data_analyst")

    missing_ids = {s["skill_id"] for s in data_analyst["missing_skills"]}
    assert "python" in missing_ids  # javascript/python is still an excluded pair
    assert not any("Python" in note for note in data_analyst["caveats"])


def test_all_twelve_exclusion_pairs_still_present_with_skills_catalogue_wired():
    assert len(load_skill_not_equivalent_pairs()) == 12


# --- 6. Python + SQL student's Data Analyst skill credit ---------------------


def test_python_and_sql_student_gets_proper_data_analyst_credit_with_aliases_wired():
    profile = _profile(skills=[
        SkillRef(skill_id="python", name="Python"),
        SkillRef(skill_id="sql", name="SQL"),
    ])
    provider = HussainMatchingProvider(skills_catalogue=_real_skills_catalogue(), similarity=NO_SIMILARITY)
    result = next(
        m for m in provider.match(profile, CachedRoleCatalog().list_roles(), None, [])
        if m["role_id"] == "data_analyst"
    )
    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    missing_ids = {s["skill_id"] for s in result["missing_skills"]}
    assert {"python", "sql"} <= matched_ids
    assert "python" not in missing_ids
    assert "excel" not in missing_ids  # optional skill, never a mandatory gap


def test_sql_aliases_also_credit_the_data_analyst_sql_requirement():
    """The same student, but typing the alias "PostgreSQL" instead of the
    catalog skill_id/name "sql" — must still earn exact credit now that
    skills_catalogue carries the real alias."""
    profile = _profile(skills=[
        SkillRef(skill_id="python", name="Python"),
        SkillRef(skill_id="x", name="PostgreSQL"),
    ])
    provider = HussainMatchingProvider(skills_catalogue=_real_skills_catalogue(), similarity=NO_SIMILARITY)
    result = next(
        m for m in provider.match(profile, CachedRoleCatalog().list_roles(), None, [])
        if m["role_id"] == "data_analyst"
    )
    matched_ids = {s["skill_id"] for s in result["matched_skills"]}
    assert "sql" in matched_ids
