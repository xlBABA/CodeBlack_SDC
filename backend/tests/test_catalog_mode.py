"""Milestone 6B-3: CATALOG_MODE=fixture|cached activation behavior.

Covers: fixture stays the unchanged default; cached mode selects
CachedRoleCatalog explicitly and is reflected honestly in data_mode and
warnings; ENABLE_FIXTURES and CATALOG_MODE stay independent; invalid
cached data never silently falls back to fixture; DI overrides still
take precedence over CATALOG_MODE. Does not activate
HussainMatchingProvider, RunPod, or any real trend/roadmap/project/SDG
service — FixtureMatchingProvider is still the only scoring provider.
"""
from fastapi.testclient import TestClient

from app.api.v1.endpoints.careers import get_role_catalog
from app.core.config import Settings, get_settings
from app.main import app
from app.services.role_catalog import RoleCatalogProvider

# Milestone 13C-4: Jawad's catalog expanded from the original 8 verified
# roles to the full 30-role target (TOTAL_TARGET_ROLES in matcher.py) —
# the original 8 are unchanged, 22 new O*NET occupations were added.
CACHED_ROLE_IDS = {
    "accountant", "actuary", "aerospace_engineer", "biomedical_engineer", "budget_analyst",
    "chemical_engineer", "civil_engineer", "computer_systems_analyst", "data_analyst",
    "data_scientist", "database_administrator", "electrical_engineer", "environmental_engineer",
    "environmental_scientist", "financial_analyst", "financial_risk_specialist", "hydrologist",
    "industrial_engineer", "information_security_analyst", "logistician", "management_analyst",
    "market_research_analyst", "mechanical_engineer", "operations_research_analyst",
    "public_health_analyst", "software_developer", "statistician", "surveyor",
    "urban_regional_planner", "web_developer",
}
OVERLAP_ROLE_IDS = {"data_analyst", "financial_analyst"}
CACHED_ONLY_ROLE_IDS = {"mechanical_engineer", "public_health_analyst"}

EMPTY_PROFILE = {"interests": [], "skills": [], "projects": []}


def _override_settings(**overrides):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, **overrides)


def _clear_override():
    app.dependency_overrides.pop(get_settings, None)


# --- Fixture default is unchanged ---------------------------------------


def test_fixture_mode_is_the_default_and_unchanged(client: TestClient):
    response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 6})
    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "fixture"
    role_ids = {m["role_id"] for m in body["data"]["matches"]}
    assert role_ids == {
        "data_analyst", "financial_analyst", "mechanical_design_engineer", "sustainability_coordinator",
    }
    assert not any("CATALOG_MODE" in w for w in body["warnings"])


# --- Cached mode: catalog selection --------------------------------------


def test_cached_mode_catalog_provider_returns_exactly_the_canonical_role_set():
    """The underlying provider, not the limit<=6-constrained HTTP route,
    is the right place to assert the full canonical role set — see
    test_role_catalog_cached.py for the authoritative version of this
    check; this just confirms get_role_catalog() wires to it."""
    from app.core.config import Settings
    from app.api.v1.endpoints.careers import get_role_catalog

    catalog = get_role_catalog(Settings(CATALOG_MODE="cached", _env_file=None))
    role_ids = {role.role_id for role in catalog.list_roles()}
    assert role_ids == CACHED_ROLE_IDS


def test_cached_mode_returns_only_canonical_role_ids_via_api(client: TestClient):
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 6})
    finally:
        _clear_override()

    assert response.status_code == 200
    role_ids = {m["role_id"] for m in response.json()["data"]["matches"]}
    assert len(role_ids) == 6
    assert role_ids <= CACHED_ROLE_IDS  # MatchRequest.limit<=6 means not every role fits in one call


def test_cached_mode_matches_via_api_without_crashing(client: TestClient):
    """Fix 2 (min_semester=None) and Fix 1 (required/optional) from
    Milestone 6B-2 must hold via the real HTTP path too, not just a
    synthetic test role. MatchRequest.limit's frozen contract maximum is
    6, so this cannot exercise all 8 cached roles in one call — see
    test_hussain_matching_adapter.py / test_matching_mode.py for
    all-eight-roles coverage that bypasses that limit."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/careers/match",
            json={"profile": {"interests": [], "skills": [{"skill_id": "sql", "name": "SQL"}], "projects": []}, "limit": 6},
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    matches = response.json()["data"]["matches"]
    assert len(matches) == 6
    for match in matches:
        assert 0.0 <= match["score"] <= 100.0
        assert 0.0 <= match["score_breakdown"]["prerequisites"] <= 100.0


# --- Provenance / data_mode ----------------------------------------------


def test_cached_mode_with_fixtures_enabled_still_labels_response_fixture(client: TestClient):
    """CATALOG_MODE=cached supplies real, cached role/skill inputs, but
    the generated output (score, score_breakdown) is still entirely
    FixtureMatchingProvider — data_mode must stay "fixture", never
    "cached", even with ENABLE_FIXTURES=True (the default) explicit."""
    _override_settings(CATALOG_MODE="cached", ENABLE_FIXTURES=True)
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.json()["data_mode"] == "fixture"


def test_cached_mode_never_claims_live(client: TestClient):
    for catalog_mode in ("fixture", "cached"):
        _override_settings(CATALOG_MODE=catalog_mode)
        try:
            response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
        finally:
            _clear_override()
        assert response.json()["data_mode"] != "live"


def test_cached_mode_discloses_mixed_provenance_via_warning(client: TestClient):
    """A single data_mode value can't say both "role/skill inputs are
    cached" and "the generated output is still fixture-based" — the gap
    is covered by an explicit warning, not silently dropped. The warning
    must disclose the real cached inputs without implying the sourced
    roles themselves are fictional."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    warnings_text = " ".join(response.json()["warnings"]).lower()
    assert "cached" in warnings_text  # discloses the real cached role/skill inputs
    assert "fixture" in warnings_text  # discloses the fixture-generated output
    # Must not claim the sourced roles are fictional/invented — only the
    # generated output (scores, resources, projects) is.
    assert "roles themselves are real" in warnings_text or "are real" in warnings_text
    assert "roles are fictional" not in warnings_text


def test_cached_mode_preserves_estimated_alignment_disclaimer(client: TestClient):
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    for match in response.json()["data"]["matches"]:
        assert match["score_type"] == "profile_alignment_estimate"
        assert "hiring" in " ".join(match["caveats"]).lower()


def test_cached_mode_provenance_warning_propagates_to_roadmap_and_projects(client: TestClient):
    """All five matching-dependent endpoints share the same
    catalog_data_mode()/catalog_provenance_warnings() helpers — data_mode
    stays "fixture" everywhere, and the cached-input disclosure appears
    consistently, not just on /careers/match.

    Milestone (Jawad fix, 2026-10-25): project_provenance_warnings() used
    to say "not fixture placeholders" — internal jargon. It now says "not
    placeholder data" instead, so the literal word "fixture" is no longer
    guaranteed in the projects response specifically (it still appears on
    roadmap, from a different, untouched source); check for the intended
    disclosure — real/cached data, no internal jargon — directly instead."""
    _override_settings(CATALOG_MODE="cached")
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        projects = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear_override()

    assert roadmap.json()["data_mode"] == "fixture"
    assert projects.json()["data_mode"] == "fixture"
    assert any("cached" in w.lower() for w in roadmap.json()["warnings"])
    assert any("cached" in w.lower() for w in projects.json()["warnings"])
    assert any("fixture" in w.lower() for w in roadmap.json()["warnings"])
    assert any("placeholder" in w.lower() for w in projects.json()["warnings"])
    for warnings in (roadmap.json()["warnings"], projects.json()["warnings"]):
        joined = " ".join(warnings).lower()
        assert "jawad" not in joined
        assert "catalog_mode" not in joined


def test_cached_mode_all_five_matching_dependent_endpoints_stay_fixture_labeled(client: TestClient):
    """Scenarios and project-simulate too — every route that depends on
    get_role_catalog() must stay data_mode="fixture" regardless of
    CATALOG_MODE, since the HEADLINE output (scores) is still always
    fixture/heuristic — even though, as of Milestone 6D-2D, roadmap
    resources and recommended/simulated projects are now genuinely
    cached content when CATALOG_MODE=cached (see
    test_resource_catalog_cached_provider.py / test_project_catalog_cached_provider.py's
    now-activated-route tests for that distinction)."""
    _override_settings(CATALOG_MODE="cached")
    try:
        careers = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
        scenarios = client.post(
            "/api/v1/scenarios/simulate", json={"profile": EMPTY_PROFILE, "scenario_id": "moderate"}
        )
        roadmaps = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        recommend = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE,
                "role_id": "data_analyst",
                "project_id": "da_online_retail_dashboard",  # a real cached project_id
            },
        )
    finally:
        _clear_override()

    for response in (careers, scenarios, roadmaps, recommend, simulate):
        assert response.status_code == 200
        assert response.json()["data_mode"] == "fixture"


def test_cached_mode_projects_recommend_stays_fixture_labeled_even_with_real_cached_ids(client: TestClient):
    """As of Milestone 6D-2D, /projects/recommend under CATALOG_MODE=
    cached returns genuinely real project_ids/source_ids from
    CachedProjectCatalog (no longer FixtureProjectCatalog's synthetic
    "project_data_dashboard_001" style placeholders) — yet data_mode
    must still stay "fixture", conservatively, because which projects
    get selected/ranked is still driven by a fixture-or-heuristic
    matching score. The real-vs-placeholder distinction is disclosed via
    project_provenance_warnings() instead of this enum value."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "fixture"
    project_ids = {p["project_id"] for p in body["data"]["projects"]}
    assert project_ids  # at least one recommendation
    assert not any(pid.startswith("project_") for pid in project_ids)  # no fixture-style id
    assert any("cached" in w.lower() for w in body["warnings"])
    # Sanity check: source_ids are now real registered sources
    # (uci_*/worldbank_wdi/etc.), never the old fixture's invented
    # "source_project_xxx_001" placeholder style.
    project = body["data"]["projects"][0]
    assert not any(sid.startswith("source_project_") for sid in project["source_ids"])


# --- Downstream compatibility: overlap vs. cached-only roles -------------


def test_cached_mode_roadmap_works_for_an_overlapping_role(client: TestClient):
    """data_analyst has real resource-catalog entries regardless of which
    role catalog supplied the role itself."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    assert response.json()["data"]["steps"]  # at least one real resource (sql/python/data_visualization)


def test_cached_mode_projects_simulate_works_for_an_overlapping_role(client: TestClient):
    """As of Milestone 6D-2D, CATALOG_MODE=cached also activates
    CachedProjectCatalog — the old fixture project_id no longer resolves
    here, so this uses a real cached project_id instead."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE,
                "role_id": "data_analyst",
                "project_id": "da_online_retail_dashboard",
            },
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    data = response.json()["data"]
    assert 0 <= data["baseline_score"] <= 100
    assert 0 <= data["simulated_score"] <= 100


def test_cached_mode_projects_recommend_is_honest_empty_for_a_fixture_only_role(client: TestClient):
    """As of Milestone 6D-2D, CachedProjectCatalog is active under
    CATALOG_MODE=cached, so mechanical_engineer now DOES have real cached
    projects (see test_project_catalog_cached_provider.py). The genuinely
    unsupported case now is a role_id outside Jawad's canonical set
    entirely — e.g. our fixture-only mechanical_design_engineer — which
    must still return an honest empty result, not a fabricated project
    borrowed from an unrelated role."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/recommend",
            json={"profile": EMPTY_PROFILE, "role_id": "mechanical_design_engineer"},
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["projects"] == []
    assert any("mechanical_design_engineer" in w for w in body["warnings"])


def test_cached_mode_projects_recommend_now_finds_real_projects_for_previously_empty_role(client: TestClient):
    """The flip side of the above: mechanical_engineer, which had no
    project under the old (pre-6D-2D) FixtureProjectCatalog-only wiring,
    now correctly returns real cached projects."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/recommend",
            json={"profile": EMPTY_PROFILE, "role_id": "mechanical_engineer"},
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["projects"]  # no longer empty
    assert body["data_mode"] == "fixture"  # still conservative (score/selection still heuristic)
    assert any("cached" in w.lower() for w in body["warnings"])


def test_cached_mode_sdgs_endpoint_now_returns_real_mappings_for_a_cached_only_role(client: TestClient):
    """As of Milestone 6D-2D, GET /sdgs/{role_id} IS gated by
    CATALOG_MODE — public_health_analyst (outside the fixture SDG
    catalog's 4 hardcoded role_ids) now correctly resolves against
    CachedSdgCatalog, with data_mode="cached" (SDG has no scoring layer
    riding on top, so this is accurate, unlike the other endpoints)."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/sdgs/public_health_analyst")
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "cached"
    assert body["data"]["role_sdg_mappings"]  # real mapping found
    assert any("united nations" in w.lower() for w in body["warnings"])


def test_cached_mode_sdgs_endpoint_is_honest_empty_for_a_fixture_only_role(client: TestClient):
    """mechanical_design_engineer is outside Jawad's canonical role set
    entirely (not just absent from the fixture SDG catalog) — must stay
    honest-empty even under CATALOG_MODE=cached."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/sdgs/mechanical_design_engineer")
    finally:
        _clear_override()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["role_sdg_mappings"] == []


def test_cached_mode_resource_catalog_matches_by_skill_id_not_role_id(client: TestClient):
    """public_health_analyst's required skills are keyed by skill_id (never
    role-scoped, never a resource reassigned between roles).

    As of Milestone 13D-9 (Jawad's approved "Option C" rebuild,
    origin/feat/jawad-ph-fix @ 1cf9b74), the role's required skills are
    critical_thinking, complex_problem_solving, science, systems_analysis,
    mathematics and analytical_scientific_software (sql and python became
    optional). CachedResourceCatalog covers only 3 of those 6 so far
    (complex_problem_solving, science and systems_analysis have no resource
    yet); per the "do not invent missing resources" rule, those gaps are
    omitted with a warning rather than fabricated — see the omission
    warnings this test also checks for."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/roadmaps/generate",
            json={"profile": EMPTY_PROFILE, "role_id": "public_health_analyst"},
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    step_skill_ids = {s["skill_id"] for s in body["data"]["steps"]}
    assert step_skill_ids == {"critical_thinking", "mathematics", "analytical_scientific_software"}
    for missing in ("complex_problem_solving", "science", "systems_analysis"):
        assert any(
            f"No placeholder resource is available yet for skill '{missing}'" in w for w in body["warnings"]
        ), missing
    fixture_resource_ids = {
        "resource_sql_basics_001", "resource_python_basics_001", "resource_dataviz_basics_001",
        "resource_excel_basics_001", "resource_finmodel_basics_001", "resource_cad_basics_001",
        "resource_sustainability_reporting_001",
    }
    for step in body["data"]["steps"]:
        assert step["resource_id"] not in fixture_resource_ids
    assert any("cached" in w.lower() for w in body["warnings"])


def test_cached_mode_unknown_role_behaves_consistently(client: TestClient):
    _override_settings(CATALOG_MODE="cached")
    try:
        roadmap = client.post(
            "/api/v1/roadmaps/generate",
            json={"profile": EMPTY_PROFILE, "role_id": "does_not_exist_anywhere"},
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE,
                "role_id": "does_not_exist_anywhere",
                "project_id": "project_data_dashboard_001",
            },
        )
    finally:
        _clear_override()

    assert roadmap.status_code == 200
    assert roadmap.json()["data"]["steps"] == []
    assert simulate.status_code == 404
    assert simulate.json()["error"]["code"] == "ROLE_NOT_FOUND"


# --- Independence from ENABLE_FIXTURES, and safe failure modes ----------


def test_enable_fixtures_false_still_blocks_matching_in_cached_mode(client: TestClient):
    """CATALOG_MODE=cached must not weaken the existing ENABLE_FIXTURES=
    False safeguard — real scoring is still unimplemented regardless of
    which role catalog is selected."""
    _override_settings(CATALOG_MODE="cached", ENABLE_FIXTURES=False)
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"


def test_invalid_cached_data_does_not_silently_fall_back_to_fixture(client: TestClient, monkeypatch):
    """If the cached catalog's own validation fails, the request must
    fail loudly (503), never silently serve the fixture catalog instead."""
    import app.services.role_catalog_cached as cached_module

    def _broken_load():
        raise cached_module.CachedCatalogError("simulated corrupt cached data file")

    monkeypatch.setattr(cached_module, "load_cached_roles", _broken_load)
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 4})
    finally:
        _clear_override()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
    role_ids = response.json()  # no "data" key on an error response
    assert "data" not in role_ids


def test_invalid_cached_resource_data_fails_loud_on_roadmap_generate(client: TestClient, monkeypatch):
    """Milestone 6D-2D: corrupt cached resources.json must 503 the newly
    activated /roadmaps/generate route, never silently serve
    FixtureResourceCatalog instead."""
    import app.services.resource_catalog_cached as cached_module

    def _broken_load():
        raise cached_module.CachedCatalogError("simulated corrupt cached resources file")

    monkeypatch.setattr(cached_module, "load_cached_resources", _broken_load)
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/roadmaps/generate", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
    finally:
        _clear_override()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
    assert "data" not in response.json()


def test_invalid_cached_project_data_fails_loud_on_projects_recommend_and_simulate(
    client: TestClient, monkeypatch
):
    """Milestone 6D-2D: corrupt cached projects.json must 503 both
    newly activated project routes, never silently serve
    FixtureProjectCatalog instead."""
    import app.services.project_catalog_cached as cached_module

    def _broken_load():
        raise cached_module.CachedCatalogError("simulated corrupt cached projects file")

    monkeypatch.setattr(cached_module, "load_cached_projects", _broken_load)
    _override_settings(CATALOG_MODE="cached")
    try:
        recommend = client.post(
            "/api/v1/projects/recommend", json={"profile": EMPTY_PROFILE, "role_id": "data_analyst"}
        )
        simulate = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE,
                "role_id": "data_analyst",
                "project_id": "da_online_retail_dashboard",
            },
        )
    finally:
        _clear_override()

    for response in (recommend, simulate):
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
        assert "data" not in response.json()


def test_invalid_cached_sdg_data_fails_loud_on_sdgs_endpoint(client: TestClient, monkeypatch):
    """Milestone 6D-2D: corrupt cached sdg_mappings.json must 503
    GET /sdgs/{role_id} in cached mode, never silently serve
    FixtureSdgCatalog instead."""
    import app.api.v1.endpoints.sdgs as sdgs_endpoint
    import app.services.sdg_catalog_cached as cached_module

    def _broken_load():
        raise cached_module.CachedCatalogError("simulated corrupt cached sdg mappings file")

    # sdgs.py's eager validation calls its own `from ... import
    # load_cached_sdg_mappings`-bound name, not a module-qualified
    # lookup — patch that name directly (patching the source module's
    # attribute alone would not affect the already-bound import).
    monkeypatch.setattr(sdgs_endpoint, "load_cached_sdg_mappings", _broken_load)
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/sdgs/data_analyst")
    finally:
        _clear_override()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
    assert "data" not in response.json()


def test_cached_mode_sdgs_endpoint_preserves_multiple_sdgs_per_role_end_to_end(client: TestClient):
    """Milestone 6D-2D: hitting the real, activated route (not just the
    service/catalog unit tests from 6D-2C) for a role with 2 SDGs."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/sdgs/civil_engineer")
    finally:
        _clear_override()

    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "cached"
    sdg_ids = {m["sdg_id"] for m in body["data"]["role_sdg_mappings"]}
    assert sdg_ids == {9, 11}
    assert any("united nations" in w.lower() for w in body["warnings"])


# --- DI overrides remain functional ---------------------------------------


def test_role_catalog_di_override_takes_precedence_over_catalog_mode(client: TestClient):
    class StubCatalog:
        def list_roles(self) -> list:
            from app.services.role_catalog import RoleFixture, RoleRequirement

            return [
                RoleFixture(
                    role_id="stub_role",
                    role_title="Stub Role",
                    category="Test",
                    min_semester=1,
                    required_skills=(RoleRequirement("sql", "SQL", weight=1.0),),
                    transferable_interests=(),
                    evidence_ids=("stub_evidence",),
                )
            ]

    _override_settings(CATALOG_MODE="cached")
    app.dependency_overrides[get_role_catalog] = lambda: StubCatalog()
    try:
        response = client.post("/api/v1/careers/match", json={"profile": EMPTY_PROFILE, "limit": 6})
    finally:
        _clear_override()
        app.dependency_overrides.pop(get_role_catalog, None)

    assert response.status_code == 200
    role_ids = {m["role_id"] for m in response.json()["data"]["matches"]}
    assert role_ids == {"stub_role"}


def test_get_role_catalog_returns_cached_role_catalog_instance_directly():
    """Unit-level confirmation, bypassing HTTP: get_role_catalog(settings)
    actually returns a CachedRoleCatalog, not merely cached-shaped data."""
    from app.services.role_catalog_cached import CachedRoleCatalog

    settings = Settings(CATALOG_MODE="cached", _env_file=None)
    catalog: RoleCatalogProvider = get_role_catalog(settings)
    assert isinstance(catalog, CachedRoleCatalog)


def test_get_role_catalog_returns_fixture_role_catalog_by_default():
    from app.services.role_catalog import FixtureRoleCatalog

    settings = Settings(_env_file=None)
    catalog: RoleCatalogProvider = get_role_catalog(settings)
    assert isinstance(catalog, FixtureRoleCatalog)
