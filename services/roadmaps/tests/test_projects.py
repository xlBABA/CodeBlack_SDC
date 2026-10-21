"""Run from the repo root: python -m services.roadmaps.tests.test_projects"""
import json
import re
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from services.roadmaps import get_projects

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))["projects"]
SKILL_IDS = {s["skill_id"] for s in json.loads((ROOT / "data" / "skills.json").read_text(encoding="utf-8"))["skills"]}
ROLE_IDS = [r["role_id"] for r in json.loads((ROOT / "data" / "roles.json").read_text(encoding="utf-8"))]
REGISTER = (ROOT / "docs" / "source-register.md").read_text(encoding="utf-8")
REGISTERED = set(re.findall(r"^\| ([a-z0-9_]+) \|", REGISTER, flags=re.M))


# Field-for-field copy of RecommendedProject / ProjectRecommendationPayload from
# origin/feature/rehan-backend-foundation:backend/app/schemas/projects.py (commit 66614f2).
# Re-copy if that file changes.
class RecommendedProject(BaseModel):
    project_id: str
    title: str
    skill_ids: list[str]
    estimated_hours: float = Field(ge=0)
    source_ids: list[str]
    milestones: list[str]


class ProjectRecommendationPayload(BaseModel):
    projects: list[RecommendedProject]


def test_every_project_fits_rehans_recommended_project():
    for p in PROJECTS:
        RecommendedProject.model_validate(p)  # raises on mismatch


def test_get_projects_output_fits_rehans_payload_for_every_role():
    for role_id in ROLE_IDS:
        data = get_projects(role_id, limit=10)
        ProjectRecommendationPayload.model_validate(data)
        assert 2 <= len(data["projects"]) <= 3, role_id


def test_every_skill_id_exists():
    for p in PROJECTS:
        assert set(p["skill_ids"]) <= SKILL_IDS, (p["project_id"], set(p["skill_ids"]) - SKILL_IDS)


def test_every_source_id_is_registered():
    for p in PROJECTS:
        assert p["source_ids"], p["project_id"]
        assert set(p["source_ids"]) <= REGISTERED, (p["project_id"], set(p["source_ids"]) - REGISTERED)


def test_hours_numeric_ge_0_and_match_the_milestone_sum():
    for p in PROJECTS:
        assert isinstance(p["estimated_hours"], (int, float)) and p["estimated_hours"] >= 0
        assert p["hours_basis"] == "team_estimate"
        parts = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", p["hours_basis_note"])]
        assert sum(parts) == p["estimated_hours"], p["project_id"]
        assert len(parts) == len(p["milestones"]), p["project_id"]


def test_milestones_are_4_to_6_plain_strings():
    for p in PROJECTS:
        assert 4 <= len(p["milestones"]) <= 6, p["project_id"]
        assert all(isinstance(m, str) and m for m in p["milestones"])


def test_ids_unique_and_roles_real():
    ids = [p["project_id"] for p in PROJECTS]
    assert len(ids) == len(set(ids))
    assert {p["role_id"] for p in PROJECTS} == set(ROLE_IDS)


def test_nothing_is_called_trending():
    assert "trending" not in json.dumps(PROJECTS).lower()


def test_requested_notes_are_present():
    by_id = {p["project_id"]: p for p in PROJECTS}
    note = by_id["ph_diabetes_readmission"]["data_note"]
    assert "de-identified" in note and "CC BY 4.0" in note and "No part of it is included" in note
    assert by_id["me_parametric_bracket_cad"]["source_type"] == "tutorial"
    assert "exclude sex, marital status and age" in " ".join(by_id["fa_credit_default_analysis"]["milestones"])


def test_limit_and_unknown_role():
    assert len(get_projects("mechanical_engineer", limit=1)["projects"]) == 1
    assert len(get_projects("mechanical_engineer")["projects"]) == 3  # default limit 3
    assert get_projects("mechanical_engineer", limit=0) == {"projects": []}
    assert get_projects("no_such_role") is None


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
