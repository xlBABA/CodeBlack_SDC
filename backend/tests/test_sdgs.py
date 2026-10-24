import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.sdgs import get_sdg_catalog
from app.main import app
from app.services.sdg_catalog import FixtureSdgCatalog

# Phrases that would constitute an affirmative false claim of official
# certification/endorsement — the thing section E explicitly forbids
# ("Do not claim United Nations endorsement or official certification").
# Deliberately phrase-based rather than a single bare substring (like
# "certifi"), because the legitimate fixture disclaimer text itself
# contains "certified" inside "not a certified... claim" — see
# LEGITIMATE_DISCLAIMERS below, which this list must never match.
FALSE_CERTIFICATION_PHRASES = (
    "is certified",
    "is endorsed",
    "official certification",
    "officially certified",
    "certified by",
    "endorsed by",
    "un-certified",
    "un certified",
)
# "official certification"/"officially certified" are matched even when
# negated (e.g. "not an official certification") — deliberately
# conservative, since that phrase never appears in the real fixture
# catalog's disclaimer style (which says "not a certified... claim",
# never "official certification"). A reason using that specific phrase at
# all is worth a human double-checking.

# Representative sentences containing an affirmative false claim — the
# stronger test must flag every one of these.
FALSE_CERTIFICATION_EXAMPLES = (
    "This mapping has official certification from the United Nations.",
    "This skill is certified by the UN SDG program.",
    "This role is UN-certified for sustainability impact.",
    "This mapping is UN certified.",
    "This skill is endorsed by the United Nations.",
    "Endorsed by the UN Sustainable Development committee.",
    "This role has received official certification.",
    "This association is officially certified as SDG-aligned.",
)

# Legitimate disclaimer phrasing actually used (or representative of what's
# used) in app/services/sdg_catalog.py's fixture reasons — the stronger
# test must NOT flag any of these.
LEGITIMATE_DISCLAIMERS = (
    "Illustrative demonstration mapping: data analysis skills generally "
    "support resilient infrastructure and innovation capacity (SDG 9); a "
    "general skill-to-goal association, not a certified or externally "
    "sourced claim.",
    "Illustrative demonstration mapping: financial analysis skills "
    "generally support decent work and economic growth (SDG 8); a general "
    "association, not a sourced claim.",
    "Illustrative demonstration mapping: clear data visualization supports "
    "public understanding and quality education (SDG 4); a general "
    "association only.",
    "A general association between this skill and the stated goal; not a "
    "certified or externally sourced claim.",
)


def _contains_false_certification_claim(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in FALSE_CERTIFICATION_PHRASES)


def test_openapi_includes_sdgs_route():
    schema = app.openapi()
    assert "/api/v1/sdgs/{role_id}" in schema["paths"]
    assert "get" in schema["paths"]["/api/v1/sdgs/{role_id}"]


def test_sdgs_known_role_has_explicit_reasons(client: TestClient):
    response = client.get("/api/v1/sdgs/data_analyst")
    assert response.status_code == 200

    body = response.json()
    assert body["data_mode"] == "fixture"
    data = body["data"]
    assert len(data["role_sdg_mappings"]) >= 1
    assert len(data["skill_sdg_mappings"]) >= 1
    for mapping in data["role_sdg_mappings"] + data["skill_sdg_mappings"]:
        assert 1 <= mapping["sdg_id"] <= 17
        assert mapping["reason"]  # non-empty, explicit justification
    assert any("united nations" in w.lower() for w in body["warnings"])


def test_sdgs_unknown_role_returns_honest_empty_response(client: TestClient):
    response = client.get("/api/v1/sdgs/no_such_role")
    assert response.status_code == 200

    data = response.json()["data"]
    assert data["role_sdg_mappings"] == []
    assert data["skill_sdg_mappings"] == []


@pytest.mark.parametrize("false_claim", FALSE_CERTIFICATION_EXAMPLES)
def test_false_certification_detector_flags_representative_false_claims(false_claim: str):
    assert _contains_false_certification_claim(false_claim)


@pytest.mark.parametrize("disclaimer", LEGITIMATE_DISCLAIMERS)
def test_false_certification_detector_allows_legitimate_disclaimers(disclaimer: str):
    assert not _contains_false_certification_claim(disclaimer)


def test_sdgs_do_not_claim_official_certification(client: TestClient):
    response = client.get("/api/v1/sdgs/data_analyst")
    body = response.json()

    reasons = [
        m["reason"] for m in body["data"]["role_sdg_mappings"] + body["data"]["skill_sdg_mappings"]
    ]
    assert reasons  # the endpoint actually returned reasons to check
    for reason in reasons:
        assert not _contains_false_certification_claim(reason)


def test_sdg_fixture_catalog_reasons_contain_no_false_certification_claim():
    """Scans every reason in the real fixture catalog directly (not just
    data_analyst's), so adding a role later is covered automatically."""
    catalog = FixtureSdgCatalog()
    checked_role_ids = ("data_analyst", "financial_analyst", "mechanical_design_engineer", "sustainability_coordinator")

    for role_id in checked_role_ids:
        mapping_set = catalog.get(role_id)
        assert mapping_set is not None
        for mapping in (*mapping_set.role_sdg, *mapping_set.skill_sdg):
            assert not _contains_false_certification_claim(mapping.reason)


def test_sdg_catalog_dependency_is_overridable(client: TestClient):
    class StubSdgCatalog:
        def get(self, role_id):
            return None

    app.dependency_overrides[get_sdg_catalog] = lambda: StubSdgCatalog()
    try:
        response = client.get("/api/v1/sdgs/data_analyst")
    finally:
        del app.dependency_overrides[get_sdg_catalog]

    data = response.json()["data"]
    assert data["role_sdg_mappings"] == []
