"""Names that are only part of a skill name, or contain a skill name (no model needed).

Ported verbatim from Hussain's origin/feature/hussain-matching @ 54b0906
(services/matching/tests/test_partial_names.py), with only the import
path changed to this vendored package's actual location
(app.services.hussain_matching, not services.matching).
"""
import pytest

from app.services.hussain_matching import Matcher, SkillNormalizer
from app.services.hussain_matching.scoring import RELATED_CREDIT

SKILLS = [
    {"skill_id": "python", "name": "Python", "aliases": ["Python3"]},
    {"skill_id": "excel", "name": "Excel", "aliases": ["Microsoft Excel"]},
    {"skill_id": "sql", "name": "SQL", "aliases": ["Structured Query Language"]},
    {"skill_id": "javascript", "name": "JavaScript", "aliases": ["JS"]},
    {"skill_id": "accounting_software", "name": "Accounting Software", "aliases": ["QuickBooks"]},
    {"skill_id": "financial_analysis_software", "name": "Financial Analysis Software", "aliases": []},
    {"skill_id": "cad_software", "name": "CAD Software", "aliases": []},
    {"skill_id": "statistical_software", "name": "Statistical Software", "aliases": []},
]
ROLE = {
    "role_id": "analyst", "role_title": "Analyst", "verified": True,
    "required_skills": [{"skill_id": "python", "importance": 1.0, "required": True},
                        {"skill_id": "excel", "importance": 1.0, "required": True}],
    "prerequisites": [],
}


@pytest.fixture
def normalizer():
    return SkillNormalizer(SKILLS)


def interpret(normalizer, *names, interpreter=None):
    return normalizer.interpret_profile_skills([{"name": n} for n in names], interpreter)


# ---- a fragment of a longer skill name: ask, do not guess ----

def test_part_of_a_longer_name_is_not_mapped_and_gets_a_suggestion(normalizer):
    resolved, warnings, interpreted = interpret(normalizer, "Accounting")
    assert resolved == {} and interpreted == {}
    assert len(warnings) == 1
    assert warnings[0].startswith("Skill 'Accounting' is not in the supported catalogue")
    assert warnings[0].endswith("Did you mean Accounting Software?")


def test_the_suggestion_wins_over_an_embedding_match(normalizer):
    asked = []

    def eager_interpreter(names):
        asked.extend(names)
        return [("accounting_software", 0.77)] * len(names)  # what RunPod measured live

    resolved, warnings, interpreted = interpret(normalizer, "Accounting", interpreter=eager_interpreter)
    assert resolved == {} and interpreted == {}
    assert asked == []  # not even offered to the interpreter
    assert "Did you mean Accounting Software?" in warnings[0]


def test_up_to_three_suggestions_are_listed_more_are_too_vague(normalizer):
    _, warnings, _ = interpret(normalizer, "Software")  # 4 skills have it in their name
    assert "Did you mean" not in warnings[0]
    _, warnings, _ = interpret(normalizer, "Analysis Software")
    assert warnings[0].endswith("Did you mean Financial Analysis Software?")
    skills = [s for s in SKILLS if s["skill_id"] != "statistical_software"]
    _, warnings, _ = interpret(SkillNormalizer(skills), "Software")
    assert warnings[0].endswith("Did you mean Accounting Software, CAD Software or Financial Analysis Software?")


def test_no_suggestion_for_tiny_text_or_when_the_skill_is_already_held(normalizer):
    assert "Did you mean" not in interpret(normalizer, "AI")[1][0]
    _, warnings, _ = interpret(normalizer, "Accounting Software", "Accounting")
    assert len(warnings) == 1 and "Did you mean" not in warnings[0]
    assert "Skill 'Accounting' is not in the supported catalogue" in warnings[0]


# ---- a phrase that contains exactly one known skill: map it, ask to confirm ----

def test_text_containing_one_known_skill_is_mapped_with_a_confirm_caveat(normalizer):
    resolved, warnings, interpreted = interpret(normalizer, "Python (pandas)")
    assert resolved == {"python": None}
    assert warnings == ['Interpreted "Python (pandas)" as Python (it contains "Python"), partial credit; please confirm.']
    assert interpreted["python"].contains == "Python"


def test_contained_skill_works_without_any_interpreter_or_model(normalizer):
    resolved, _, _ = normalizer.interpret_profile_skills([{"name": "Advanced Excel"}], None)
    assert resolved == {"excel": None}


def test_longest_matching_phrase_is_reported(normalizer):
    _, _, interpreted = interpret(normalizer, "Advanced Microsoft Excel")
    assert interpreted["excel"].contains == "Microsoft Excel"


def test_two_known_skills_in_one_phrase_are_not_guessed(normalizer):
    resolved, warnings, _ = interpret(normalizer, "Python and SQL")
    assert resolved == {}
    assert "not in the supported catalogue" in warnings[0]


def test_whole_words_only(normalizer):
    for text in ("Excellence", "JSON parsing", "Pythonic style"):
        resolved, _, _ = interpret(normalizer, text)
        assert resolved == {}, text


def test_a_confirmed_skill_beats_the_contained_one(normalizer):
    resolved, warnings, interpreted = interpret(normalizer, "Excel", "Advanced Excel")
    assert resolved == {"excel": None} and interpreted == {}
    assert warnings == []


def test_proficiency_is_kept(normalizer):
    resolved, _, _ = normalizer.interpret_profile_skills(
        [{"name": "Python (pandas)", "proficiency": "advanced"}])
    assert resolved == {"python": "advanced"}


# ---- through the matcher: partial credit and a caveat on the roles that use it ----

def score(normalizer, *names):
    data = Matcher(normalizer).match_roles({"skills": [{"name": n} for n in names]}, [ROLE], limit=3)
    return data["matches"][0], data["warnings"]


def test_contained_skill_earns_partial_credit_and_a_caveat(normalizer):
    exact, _ = score(normalizer, "Python", "Excel")
    contained, warnings = score(normalizer, "Python (pandas)", "Excel")
    only_excel, _ = score(normalizer, "Excel")
    assert only_excel["score_breakdown"]["skills"] < contained["score_breakdown"]["skills"] < exact["score_breakdown"]["skills"]
    # Python at RELATED_CREDIT, Excel in full: 0.85 * (0.5 + 1) / 2
    assert contained["score_breakdown"]["skills"] == round(100 * 0.85 * (RELATED_CREDIT + 1) / 2)
    note = 'Interpreted "Python (pandas)" as Python (it contains "Python"), partial credit; please confirm.'
    assert note in contained["caveats"] and note in warnings


def test_a_suggestion_gives_no_credit(normalizer):
    match, warnings = score(normalizer, "Accounting")
    assert match["score_breakdown"]["skills"] == 0
    assert any("Did you mean Accounting Software?" in w for w in warnings)
