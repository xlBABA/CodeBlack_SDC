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


ORIGINAL_4 = ["data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst"]
ADDED_4 = ["software_developer", "accountant", "civil_engineer", "environmental_scientist"]


def test_original_four_roles_still_exist_unchanged_order():
    assert [r["role_id"] for r in get_roles()][:4] == ORIGINAL_4


def test_all_eight_roles_are_verified_and_unique():
    roles = get_roles()
    ids = [r["role_id"] for r in roles]
    assert ids == ORIGINAL_4 + ADDED_4
    assert len(set(ids)) == len(ids)
    assert all(r["verified"] is True for r in roles)


def test_no_existing_id_was_removed_or_renamed():
    root = Path(__file__).resolve().parents[3] / "data"
    load = lambda n: json.loads((root / n).read_text(encoding="utf-8"))
    skills = {s["skill_id"] for s in load("skills.json")["skills"]}
    resources = {r["resource_id"] for r in load("resources.json")["resources"]}
    projects = {p["project_id"] for p in load("projects.json")["projects"]}
    assert {
        "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis", "attention_to_detail",
        "excel", "sql", "python", "data_visualization", "cad_software", "matlab",
        "financial_analysis_software", "analytical_scientific_software", "vba",
    } <= skills
    assert {
        "mslearn_tsql_query_modify", "mslearn_python_part1_fundamentals", "mslearn_power_bi_prepare_visualize",
        "mslearn_vba_getting_started_office", "mathworks_matlab_onramp", "fcc_statistics_video_monika_wahi",
        "mit_ocw_18_05_probability_statistics", "sas_programming_1_essentials", "fcc_excel_beginners_full_course",
        "alison_thinking_critically", "onshape_cad_basics_pathway",
    } <= resources
    assert {
        "da_online_retail_dashboard", "da_bank_campaign_analysis", "fa_macro_indicator_workbook",
        "fa_credit_default_analysis", "me_predictive_maintenance", "me_power_plant_regression",
        "me_parametric_bracket_cad", "ph_diabetes_readmission", "ph_health_indicator_trends",
    } <= projects


def test_two_roles_per_industry_bucket():
    from collections import Counter
    assert Counter(r["industry_category"] for r in get_roles()) == {
        "Technology & AI": 2, "Business & Finance": 2,
        "Engineering & Manufacturing": 2, "Healthcare & Sustainability": 2,
    }


def test_new_roles_use_exact_onet_titles():
    titles = {r["role_id"]: r["onet_title"] for r in get_roles()}
    assert titles["accountant"] == "Accountants and Auditors"
    assert titles["environmental_scientist"] == "Environmental Scientists and Specialists, Including Health"
    assert titles["software_developer"] == "Software Developers"
    assert titles["civil_engineer"] == "Civil Engineers"


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


def test_data_analyst_has_python_with_onet_source():
    da = get_role("data_analyst")
    py = next(s for s in da["required_skills"] if s["skill_id"] == "python")
    assert (py["importance"], py["required"]) == (3, True)
    assert "NOT found" not in da["notes"] and "15-2051.01/43232405" in da["notes"]
    skills = json.loads((Path(__file__).resolve().parents[3] / "data" / "skills.json").read_text(encoding="utf-8"))
    assert "onet_15_2051_01" in next(s for s in skills["skills"] if s["skill_id"] == "python")["source_ids"]


def test_not_equivalent_pairs_use_real_skill_ids():
    root = Path(__file__).resolve().parents[3]
    doc = json.loads((root / "data" / "skill_not_equivalent.json").read_text(encoding="utf-8"))
    assert list(doc) == ["not_equivalent"]  # exactly Hussain's format, nothing else
    pairs = doc["not_equivalent"]
    for pair in pairs:
        assert len(pair) == 2 and pair[0] != pair[1], pair
        assert set(pair) <= set(SKILLS), set(pair) - set(SKILLS)
    assert len({frozenset(p) for p in pairs}) == len(pairs), "duplicate pair"
    assert not {frozenset(p) for p in pairs} & {frozenset(["programming", "python"]), frozenset(["programming", "javascript"])}
    register = (root / "docs" / "source-register.md").read_text(encoding="utf-8")
    for a, b in pairs:  # every pair has its reason in the source register
        assert f"| {a} / {b} |" in register, (a, b)


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
