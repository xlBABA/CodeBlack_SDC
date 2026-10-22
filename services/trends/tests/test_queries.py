import json
from pathlib import Path

from services.trends.queries import COVERED_SKILLS, NOT_COVERED_SKILLS

SKILLS_PATH = Path(__file__).resolve().parents[3] / "data" / "skills.json"


def test_every_catalogue_skill_is_covered_or_explicitly_excluded():
    skill_ids = {s["skill_id"] for s in json.loads(SKILLS_PATH.read_text(encoding="utf-8"))["skills"]}
    covered = set(COVERED_SKILLS)
    excluded = set(NOT_COVERED_SKILLS)
    missing = skill_ids - covered - excluded
    assert not missing, f"Skills with no coverage decision at all: {missing}"
    overlap = covered & excluded
    assert not overlap, f"Skills both covered and excluded: {overlap}"


def test_every_exclusion_has_a_real_reason():
    for skill_id, reason in NOT_COVERED_SKILLS.items():
        assert len(reason) > 20, f"{skill_id}: exclusion reason too thin to be honest"


def test_no_duplicate_topics_hiding_a_copy_paste_error():
    topics = list(COVERED_SKILLS.values())
    assert len(topics) == len(set(topics)), "Two skills point at the same GitHub topic"
