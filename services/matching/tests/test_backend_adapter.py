"""Adapter tests.

The first group uses small stand-ins shaped like Rehan's RoleFixture, so they
run without the backend. The last test runs against the real backend
(backend/app) when it is present in the repo, and is skipped otherwise.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from services.matching.backend_adapter import HussainMatchingProvider, role_to_matcher_format

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Req:  # same fields as app.services.role_catalog.RoleRequirement
    skill_id: str
    name: str
    weight: float = 1.0


@dataclass(frozen=True)
class Role:  # same fields as app.services.role_catalog.RoleFixture
    role_id: str
    role_title: str
    category: str
    min_semester: int
    required_skills: tuple
    transferable_interests: tuple
    evidence_ids: tuple
    verified: bool = True


DATA_ANALYST = Role(
    "data_analyst", "Data Analyst", "Technology & AI", 3,
    (Req("sql", "SQL", 1.0), Req("python", "Python", 1.0),
     Req("data_visualization", "Data Visualization", 0.8), Req("statistics", "Statistics", 0.6)),
    ("analytics", "data"), ("source_role_data_analyst_001",),
)
FIN_ANALYST = Role(
    "financial_analyst", "Financial Analyst", "Business & Finance", 4,
    (Req("excel", "Excel", 1.0), Req("accounting", "Accounting", 0.8),
     Req("financial_modeling", "Financial Modeling", 0.8)),
    ("finance", "fintech"), ("source_role_financial_analyst_001",),
)
PROFILE = {
    "education_level": "undergraduate", "degree": "Computer Science", "semester": 4,
    "interests": ["data analytics"], "projects": [],
    "skills": [{"skill_id": "sql", "name": "SQL"}, {"skill_id": "python", "name": "Python"}],
}


def test_role_conversion_keeps_weights_and_adds_semester_prereq():
    r = role_to_matcher_format(DATA_ANALYST)
    assert r["required_skills"][2] == {"skill_id": "data_visualization", "importance": 0.8, "required": True}
    assert r["prerequisites"][0]["type"] == "min_semester" and r["prerequisites"][0]["value"] == 3
    assert r["transferable_interests"] == ["analytics", "data"]


def test_adapter_ranks_and_returns_all_roles_as_dicts():
    out = HussainMatchingProvider().match(PROFILE, [FIN_ANALYST, DATA_ANALYST], None, [])
    assert [m["role_id"] for m in out] == ["data_analyst", "financial_analyst"]
    da = out[0]
    assert da["score_breakdown"]["prerequisites"] == 100  # semester 4 >= 3
    assert da["score_breakdown"]["transferable"] == 100  # "data analytics" contains both keywords


def test_adapter_uses_result_model():
    class FakeModel:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    out = HussainMatchingProvider(result_model=FakeModel).match(PROFILE, [DATA_ANALYST], None, [])
    assert out[0].role_id == "data_analyst" and isinstance(out[0].score, int)


def test_adapter_applies_scenario_signals():
    sig = [{"signal_id": "s", "skill_id": "python", "source_id": "src", "direction": "rising"}]
    base = HussainMatchingProvider().match(PROFILE, [DATA_ANALYST], None, [])[0]
    fast = HussainMatchingProvider().match(PROFILE, [DATA_ANALYST], "fast", sig)[0]
    assert fast["score_breakdown"]["skills"] > base["score_breakdown"]["skills"]
    assert "src" in fast["evidence_ids"]


def test_jawad_alias_catalogue_is_used():
    profile = {**PROFILE, "skills": [{"skill_id": "x", "name": "Structured Query Language"}]}
    skills = [{"skill_id": "sql", "name": "SQL", "aliases": ["Structured Query Language"]}]
    out = HussainMatchingProvider(skills_catalogue=skills).match(profile, [DATA_ANALYST], None, [])[0]
    assert [s["skill_id"] for s in out["matched_skills"]] == ["sql"]


def test_real_backend_integration():
    backend = REPO_ROOT / "backend"
    if not (backend / "app").is_dir():
        pytest.skip("backend/app not in this checkout")
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(backend))
    from app.schemas.matching import RoleMatch
    from app.schemas.profile import StudentProfile
    from app.services.role_catalog import FixtureRoleCatalog

    roles = FixtureRoleCatalog().list_roles()
    profile = StudentProfile(**PROFILE)
    out = HussainMatchingProvider(result_model=RoleMatch).match(profile, roles, "moderate", [])
    assert all(isinstance(m, RoleMatch) for m in out)
    assert out[0].role_id == "data_analyst"
    assert len(out) == len(roles)
