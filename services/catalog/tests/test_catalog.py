"""Run from the repo root: python -m services.catalog.tests.test_catalog"""
import json
import sys
from pathlib import Path

from services.catalog import get_role, get_roles

SKILLS = {
    s["skill_id"]: s["name"]
    for s in json.loads(
        (Path(__file__).resolve().parents[3] / "data" / "skills.json").read_text(encoding="utf-8")
    )["skills"]
}

# Fields Hussain's matcher reads (services/matching/README.md "Data expected from Jawad")
MATCHER_KEYS = {
    "role_id", "role_title", "verified", "required_skills", "transferable_skills",
    "transferable_interests", "prerequisites", "evidence_ids",
}


def test_get_roles_returns_the_four_verified_roles():
    roles = get_roles()
    assert [r["role_id"] for r in roles] == [
        "data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst"
    ]
    assert all(r["verified"] is True for r in roles)


def test_role_has_skills_prerequisites_sdg_tags_and_evidence():
    for r in get_roles():
        assert r["required_skills"], r["role_id"]
        assert isinstance(r["prerequisites"], list)
        assert r["sdg_ids"] and all(1 <= i <= 17 for i in r["sdg_ids"]), r["role_id"]
        assert r["evidence_ids"], r["role_id"]


def test_required_skills_are_skillrefs_with_real_catalogue_names():
    for r in get_roles():
        for s in r["required_skills"]:
            assert set(s) == {"skill_id", "name", "importance", "required"}
            assert s["name"] == SKILLS[s["skill_id"]]
            assert 1 <= s["importance"] <= 5


def test_roles_still_fit_hussains_matcher_format():
    for r in get_roles():
        assert MATCHER_KEYS <= set(r), MATCHER_KEYS - set(r)


def test_get_role_known_and_unknown():
    assert get_role("public_health_analyst")["sdg_ids"] == [3]
    assert get_role("no_such_role") is None


def test_get_roles_does_not_change_the_data_file():
    before = (Path(__file__).resolve().parents[3] / "data" / "roles.json").read_text(encoding="utf-8")
    get_roles()[0]["required_skills"].clear()
    after = (Path(__file__).resolve().parents[3] / "data" / "roles.json").read_text(encoding="utf-8")
    assert before == after
    assert get_roles()[0]["required_skills"]


if __name__ == "__main__":
    failed = 0
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
        except Exception as e:
            failed += 1
            print(f"FAILED: {t.__name__}: {e!r}")
    print(f"{len(tests) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
