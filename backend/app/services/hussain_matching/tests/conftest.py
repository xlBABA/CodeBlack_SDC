# Vendored from origin/feature/hussain-matching @ 61373a5 (owner: Hussain), source
# services/matching/tests/conftest.py, with import paths rewritten to this package location.
import copy
import json
from pathlib import Path

import pytest

from app.services.hussain_matching import Matcher, SkillNormalizer

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture(autouse=True)
def no_runpod_env(monkeypatch):
    """Tests never see real RunPod credentials, so none can reach the network."""
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)


@pytest.fixture(scope="session")
def skills_catalogue():
    return json.loads((FIXTURES / "skills_fixture.json").read_text())["skills"]


@pytest.fixture
def roles():
    data = json.loads((FIXTURES / "roles_fixture.json").read_text())["roles"]
    return copy.deepcopy(data)


@pytest.fixture
def normalizer(skills_catalogue):
    return SkillNormalizer(skills_catalogue)


@pytest.fixture
def matcher(normalizer):
    return Matcher(normalizer)


@pytest.fixture
def cs_student():
    """Same as contracts/examples/synthetic_student.json (fictional)."""
    return {
        "education_level": "undergraduate",
        "degree": "Computer Science",
        "semester": 4,
        "interests": ["data analytics"],
        "skills": [
            {"skill_id": "python", "name": "Python"},
            {"skill_id": "sql", "name": "SQL"},
        ],
        "projects": ["Synthetic university data-cleaning exercise"],
        "experience_summary": "No professional experience (fictional test case)",
    }


@pytest.fixture
def business_student():
    return {
        "education_level": "undergraduate",
        "degree": "Business Administration",
        "semester": 5,
        "interests": ["consulting"],
        "skills": [
            {"name": "Microsoft Excel", "proficiency": "advanced"},
            {"name": "Requirements Gathering"},
            {"name": "Communication Skills"},
            {"name": "Teamwork"},
        ],
        "projects": ["Group case study gathering requirements for a cafe app, built in Excel"],
        "experience_summary": "",
    }
