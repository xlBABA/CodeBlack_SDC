"""Run from the repo root: python -m services.roadmaps.tests.test_roadmap"""
import json
import re
import sys
from pathlib import Path

from services.roadmaps import roadmap
from services.roadmaps import get_roadmap

DATA = Path(__file__).resolve().parents[3] / "data"
RES = json.loads((DATA / "resources.json").read_text(encoding="utf-8"))
SKILL_IDS = {s["skill_id"] for s in json.loads((DATA / "skills.json").read_text(encoding="utf-8"))["skills"]}
PROFILE = {"interests": [], "skills": [], "projects": []}


# --- data/resources.json ---------------------------------------------------

def test_resource_ids_unique_and_skills_real():
    ids = [r["resource_id"] for r in RES["resources"]]
    assert len(ids) == len(set(ids))
    for r in RES["resources"]:
        assert set(r["skill_ids"]) <= SKILL_IDS, r["resource_id"]
        assert set(r["prerequisites"]["skill_ids"]) <= SKILL_IDS, r["resource_id"]


def test_every_skill_has_a_resource_or_a_stated_reason_not_both():
    with_res = {s for r in RES["resources"] for s in r["skill_ids"]}
    without = set(RES["skills_without_resource"])
    assert with_res | without == SKILL_IDS, SKILL_IDS - with_res - without
    assert not (with_res & without)
    assert all(len(v) > 20 for v in RES["skills_without_resource"].values())


def test_each_resource_has_provenance_and_honest_hours():
    for r in RES["resources"]:
        assert r["url"].startswith("https://"), r["resource_id"]
        assert r["title"] and r["provider"]
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["checked_at"])
        assert r["price"]["status"] in {"free_stated", "no_charge_observed", "not_stated", "paid"}
        if r["estimated_hours"] is None:
            assert r["hours_source"].startswith("Not stated"), r["resource_id"]
            assert r["team_estimate_hours"] > 0, r["resource_id"]
            assert r["team_estimate_basis"].startswith("Team estimate:"), r["resource_id"]
        else:
            assert r["estimated_hours"] > 0
            assert r["hours_source"].startswith("Provider-stated"), r["resource_id"]
            assert "team_estimate_hours" not in r, r["resource_id"]  # never mix the two


# --- get_roadmap -----------------------------------------------------------

def test_shape_matches_contract():
    plan = get_roadmap(PROFILE, "data_analyst", ["sql"])
    assert set(plan) == {"steps", "total_estimated_hours", "warnings"}
    assert set(plan["steps"][0]) == {"skill_id", "resource_id", "estimated_hours", "reason", "hours_basis"}


def test_data_analyst_orders_required_by_importance_and_flags_no_resource():
    plan = get_roadmap(PROFILE, "data_analyst", ["sql", "excel", "data_visualization"])
    # data_visualization (importance 5) before sql (3); excel has no verified resource
    assert [s["skill_id"] for s in plan["steps"]] == ["data_visualization", "sql"]
    assert plan["total_estimated_hours"] == 13.95  # 8.2 + 5.75, both provider-stated
    assert any("excel" in w and "No verified" in w for w in plan["warnings"])


def test_accepts_skillref_dicts_from_rolematch():
    plan = get_roadmap(PROFILE, "data_analyst", [{"skill_id": "sql", "name": "SQL"}])
    assert [s["skill_id"] for s in plan["steps"]] == ["sql"]


def test_team_estimate_used_when_provider_states_none_and_labelled():
    plan = get_roadmap(PROFILE, "mechanical_engineer", ["matlab", "python"])
    steps = {s["skill_id"]: s for s in plan["steps"]}
    assert (steps["matlab"]["estimated_hours"], steps["matlab"]["hours_basis"]) == (3.0, "team_estimate")
    assert (steps["python"]["estimated_hours"], steps["python"]["hours_basis"]) == (3.2, "provider_stated")
    assert plan["total_estimated_hours"] == 6.2  # both kinds included
    team_warnings = [w for w in plan["warnings"] if "team estimates" in w]
    assert len(team_warnings) == 1 and "matlab" in team_warnings[0] and "python" not in team_warnings[0]


def test_no_team_estimate_warning_when_all_hours_are_provider_stated():
    plan = get_roadmap(PROFILE, "data_analyst", ["sql", "data_visualization"])
    assert all(s["hours_basis"] == "provider_stated" for s in plan["steps"])
    assert not any("team estimates" in w for w in plan["warnings"])


def _every_full_plan():
    """One plan per role with ALL of that role's skills missing (widest case)."""
    roles = json.loads((DATA / "roles.json").read_text(encoding="utf-8"))
    for role in roles:
        yield get_roadmap(PROFILE, role["role_id"], [s["skill_id"] for s in role["required_skills"]])


def test_every_step_has_numeric_hours_ge_0():
    for plan in _every_full_plan():
        assert plan["total_estimated_hours"] >= 0
        for s in plan["steps"]:
            assert isinstance(s["estimated_hours"], float) and s["estimated_hours"] >= 0, s
            assert s["hours_basis"] in {"provider_stated", "team_estimate"}


def test_output_validates_against_rehans_roadmap_schema():
    # Field-for-field copy of RoadmapStep / RoadmapPayload from
    # origin/feature/rehan-backend-foundation:backend/app/schemas/roadmaps.py (commit 66614f2).
    # Re-copy if that file changes.
    from pydantic import BaseModel, Field

    class RoadmapStep(BaseModel):
        skill_id: str
        resource_id: str
        estimated_hours: float = Field(ge=0)
        reason: str

    class RoadmapPayload(BaseModel):
        steps: list[RoadmapStep]
        total_estimated_hours: float = Field(ge=0)

    for plan in _every_full_plan():
        validated = RoadmapPayload.model_validate(plan)  # raises on any mismatch
        assert len(validated.steps) == len(plan["steps"])
        assert validated.total_estimated_hours == plan["total_estimated_hours"]


def test_unmet_prerequisite_is_warned_unless_student_has_it():
    plan = get_roadmap(PROFILE, "financial_analyst", ["vba"])
    assert any("assumes excel" in w for w in plan["warnings"])
    has_excel = {"interests": [], "projects": [], "skills": [{"skill_id": "excel", "name": "Excel"}]}
    plan = get_roadmap(has_excel, "financial_analyst", ["vba"])
    assert not any("assumes" in w for w in plan["warnings"])


def test_prerequisite_comes_first_even_if_lower_priority():
    real_load = roadmap._load
    fake_res = {"resources": [
        {"resource_id": "r_vba", "skill_ids": ["vba"], "title": "V", "provider": "P",
         "estimated_hours": 1, "prerequisites": {"skill_ids": ["excel"]}},
        {"resource_id": "r_excel", "skill_ids": ["excel"], "title": "E", "provider": "P",
         "estimated_hours": 2, "prerequisites": {"skill_ids": []}},
    ]}
    roadmap._load = lambda name: fake_res if name == "resources.json" else real_load(name)
    try:
        # mechanical_engineer: excel is optional (sorts late); vba is not a role skill and
        # sorts first by priority - but vba's resource needs excel, so excel must lead.
        plan = get_roadmap(PROFILE, "mechanical_engineer", ["vba", "excel"])
        assert [s["skill_id"] for s in plan["steps"]] == ["excel", "vba"]
    finally:
        roadmap._load = real_load


def test_unknown_role_returns_none():
    assert get_roadmap(PROFILE, "no_such_role", ["sql"]) is None


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
