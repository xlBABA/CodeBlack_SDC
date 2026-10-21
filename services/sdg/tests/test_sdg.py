"""Run from the repo root: python -m services.sdg.tests.test_sdg"""
import sys

from services.catalog import get_role, get_roles
from services.sdg import get_sdg_impact


def test_exact_contract_shape():
    impact = get_sdg_impact("data_analyst")
    assert set(impact) == {"role_sdg_mappings", "skill_sdg_mappings"}
    for m in impact["role_sdg_mappings"]:
        assert set(m) == {"sdg_id", "reason"}
    for m in impact["skill_sdg_mappings"]:
        assert set(m) == {"skill_id", "sdg_id", "reason"}


def test_public_health_role_maps_to_sdg_3():
    impact = get_sdg_impact("public_health_analyst")
    assert [m["sdg_id"] for m in impact["role_sdg_mappings"]] == [3]


def test_every_role_and_every_role_skill_has_an_sdg_with_a_reason():
    for role in get_roles():
        impact = get_sdg_impact(role["role_id"])
        assert impact["role_sdg_mappings"], role["role_id"]
        mapped = {m["skill_id"] for m in impact["skill_sdg_mappings"]}
        needed = {s["skill_id"] for s in role["required_skills"]}
        assert mapped == needed, (role["role_id"], needed - mapped)
        for m in impact["role_sdg_mappings"] + impact["skill_sdg_mappings"]:
            assert 1 <= m["sdg_id"] <= 17
            assert len(m["reason"]) > 20


def test_skill_mappings_follow_the_roles_skill_order():
    role = get_role("mechanical_engineer")
    impact = get_sdg_impact("mechanical_engineer")
    assert [m["skill_id"] for m in impact["skill_sdg_mappings"]] == [s["skill_id"] for s in role["required_skills"]]


def test_unknown_role_returns_none():
    assert get_sdg_impact("no_such_role") is None


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
