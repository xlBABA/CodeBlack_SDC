import pytest

from services.matching import SkillNormalizer


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("SQL", "sql"),
        ("structured query language", "sql"),
        ("React.js", "react"),
        ("reactjs", "react"),
        ("  Data  Visualisation ", "data_visualization"),
        ("MS Excel", "excel"),
        ("python", "python"),
    ],
)
def test_aliases_map_to_canonical_id(normalizer, raw, expected):
    assert normalizer.normalize(raw).skill_id == expected


def test_unknown_skill_is_reported_not_guessed(normalizer):
    result = normalizer.normalize("Underwater Basket Weaving")
    assert result.skill_id is None and result.method == "unknown" and result.confidence == 0


def test_profile_skills_dedupe_keeps_highest_proficiency(normalizer):
    resolved, warnings = normalizer.normalize_profile_skills(
        [
            {"name": "SQL", "proficiency": "beginner"},
            {"name": "Structured Query Language", "proficiency": "advanced"},
            {"name": "Knitting"},
        ]
    )
    assert resolved == {"sql": "advanced"}
    assert len(warnings) == 1 and "Knitting" in warnings[0]


def test_ambiguous_alias_rejected():
    with pytest.raises(ValueError, match="Ambiguous"):
        SkillNormalizer(
            [
                {"skill_id": "a", "name": "A", "aliases": ["shared"]},
                {"skill_id": "b", "name": "B", "aliases": ["shared"]},
            ]
        )


def test_duplicate_skill_id_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        SkillNormalizer([{"skill_id": "a", "name": "A"}, {"skill_id": "a", "name": "A2"}])


def test_find_in_text_uses_whole_phrases(normalizer):
    found = normalizer.find_in_text("Built a dashboards demo in Python with SQL queries")
    assert {"python", "sql", "data_visualization"} <= found
    assert "javascript" not in normalizer.find_in_text("JSON parsing")  # "js" is not inside "json"
