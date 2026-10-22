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

CACHED_ROLE_IDS = {
    "data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst",
    "software_developer", "accountant", "civil_engineer", "environmental_scientist",
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
    consistently, not just on /careers/match."""
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
    assert any("fixture" in w.lower() for w in projects.json()["warnings"])


def test_cached_mode_all_five_matching_dependent_endpoints_stay_fixture_labeled(client: TestClient):
    """Scenarios and project-simulate too — every route that depends on
    get_role_catalog() must stay data_mode="fixture" regardless of
    CATALOG_MODE, since all five still generate their headline output
    (scores, roadmap resources, recommended/simulated projects) via
    fixture providers."""
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
                "project_id": "project_data_dashboard_001",
            },
        )
    finally:
        _clear_override()

    for response in (careers, scenarios, roadmaps, recommend, simulate):
        assert response.status_code == 200
        assert response.json()["data_mode"] == "fixture"


def test_cached_mode_projects_recommend_synthetic_ids_cannot_be_labeled_cached(client: TestClient):
    """Regression guard for the exact finding from the mixed-provenance
    review: /projects/recommend's project_id/source_ids (e.g.
    "project_data_dashboard_001" / "source_project_data_dashboard_001")
    are FixtureProjectCatalog placeholders, never a real pre-registered
    source — the response must stay data_mode="fixture", not "cached",
    even in CATALOG_MODE=cached."""
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
    project = body["data"]["projects"][0]
    # Sanity check this test is exercising real synthetic placeholder
    # content, not accidentally real data.
    assert project["source_ids"] == ["source_project_data_dashboard_001"]
    assert any("not verified" in w.lower() or "fixture" in w.lower() for w in body["warnings"])


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
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/projects/simulate",
            json={
                "profile": EMPTY_PROFILE,
                "role_id": "data_analyst",
                "project_id": "project_data_dashboard_001",
            },
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    data = response.json()["data"]
    assert 0 <= data["baseline_score"] <= 100
    assert 0 <= data["simulated_score"] <= 100


def test_cached_mode_projects_recommend_is_honest_empty_for_a_cached_only_role(client: TestClient):
    """mechanical_engineer and public_health_analyst exist in Jawad's
    cached catalog but have no project_catalog.py entry (that catalog is
    still keyed to our fixture role_ids: mechanical_design_engineer,
    sustainability_coordinator) — must return an honest empty result, not
    a fabricated project borrowed from an unrelated role."""
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
    assert body["data"]["projects"] == []
    assert any("mechanical_engineer" in w for w in body["warnings"])


def test_cached_mode_sdgs_endpoint_is_honest_empty_for_a_cached_only_role(client: TestClient):
    """GET /sdgs/{role_id} has no dependency on CATALOG_MODE at all (it
    never calls get_role_catalog) — a cached-only role_id simply isn't in
    the fixture SDG catalog's 4 hardcoded role_ids either way."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.get("/api/v1/sdgs/public_health_analyst")
    finally:
        _clear_override()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["role_sdg_mappings"] == []


def test_cached_mode_resource_catalog_matches_by_skill_id_not_role_id(client: TestClient):
    """public_health_analyst (cached-only, no project_catalog entry) still
    required: critical_thinking, mathematics, sql, python — sql/python
    DO have fixture resources (keyed by skill_id, not role_id), so a
    roadmap step is produced for them precisely because resource lookup
    is never role-scoped, never because a resource was reassigned
    between roles."""
    _override_settings(CATALOG_MODE="cached")
    try:
        response = client.post(
            "/api/v1/roadmaps/generate",
            json={"profile": EMPTY_PROFILE, "role_id": "public_health_analyst"},
        )
    finally:
        _clear_override()

    assert response.status_code == 200
    step_skill_ids = {s["skill_id"] for s in response.json()["data"]["steps"]}
    assert step_skill_ids <= {"sql", "python"}
    assert step_skill_ids  # at least one real resource actually matched


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
