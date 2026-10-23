"""Run from the repo root: python -m services.catalog.tests.test_catalog"""
import json
import re
import subprocess
import sys
from pathlib import Path

from services.catalog import get_role, get_roles

ROOT = Path(__file__).resolve().parents[3]
SKILLS = {
    s["skill_id"]: s["name"]
    for s in json.loads((ROOT / "data" / "skills.json").read_text(encoding="utf-8"))["skills"]
}

# Fields Hussain's matcher reads (services/matching/README.md "Data expected from Jawad")
MATCHER_KEYS = {
    "role_id", "role_title", "verified", "required_skills", "transferable_skills",
    "transferable_interests", "prerequisites", "evidence_ids",
}


ORIGINAL_4 = ["data_analyst", "financial_analyst", "mechanical_engineer", "public_health_analyst"]
ADDED_4 = ["software_developer", "accountant", "civil_engineer", "environmental_scientist"]
ADDED_22 = [  # O*NET code in each role's onet_soc_code; see docs/source-register.md
    "data_scientist", "statistician", "operations_research_analyst", "web_developer", "database_administrator",
    "information_security_analyst", "computer_systems_analyst", "electrical_engineer", "industrial_engineer",
    "chemical_engineer", "aerospace_engineer", "surveyor", "environmental_engineer", "biomedical_engineer",
    "urban_regional_planner", "hydrologist", "management_analyst", "budget_analyst", "financial_risk_specialist",
    "actuary", "market_research_analyst", "logistician",
]


def test_original_four_roles_still_exist_unchanged_order():
    assert [r["role_id"] for r in get_roles()][:4] == ORIGINAL_4


def test_all_thirty_roles_are_verified_and_unique():
    roles = get_roles()
    ids = [r["role_id"] for r in roles]
    assert ids == ORIGINAL_4 + ADDED_4 + ADDED_22
    assert len(ids) == 30 and len(set(ids)) == len(ids)
    assert all(r["verified"] is True for r in roles)
    assert all(re.fullmatch(r"[a-z]+(_[a-z]+)*", i) for i in ids)


def test_first_eight_roles_are_byte_identical_to_the_base():
    # base = feat/jawad-data-fixes @ 9817054, the commit this branch started from
    base = subprocess.run(["git", "show", "98170543e1210c57d21d3f19d96ab44247810ea1:data/roles.json"],
                          cwd=ROOT, capture_output=True, check=True).stdout.replace(b"\r\n", b"\n")
    now = (ROOT / "data" / "roles.json").read_bytes().replace(b"\r\n", b"\n")
    old_records = base[: base.rindex(b"\n]")]  # everything before the closing bracket
    assert now.startswith(old_records + b",\n"), "an old role record changed"
    assert json.loads(now)[:8] == json.loads(base)


def test_every_role_has_four_skills_a_required_one_and_its_own_onet_source():
    roles = json.loads((ROOT / "data" / "roles.json").read_text(encoding="utf-8"))
    register = (ROOT / "docs" / "source-register.md").read_text(encoding="utf-8")
    codes = [r["onet_soc_code"] for r in roles]
    assert len(codes) == len(set(codes)), "two roles use the same O*NET occupation"
    for r in roles:
        assert len(r["required_skills"]) >= 4, r["role_id"]
        assert any(s["required"] for s in r["required_skills"]), r["role_id"]
        assert set(SKILLS) >= {s["skill_id"] for s in r["required_skills"]}, r["role_id"]
        assert r["source_id"] == "onet_" + r["onet_soc_code"].replace("-", "_").replace(".", "_"), r["role_id"]
        assert r["evidence_ids"] == [r["source_id"]], r["role_id"]
        row = next(l for l in register.splitlines() if l.startswith(f"| {r['source_id']} |"))
        assert f"https://www.onetonline.org/link/summary/{r['onet_soc_code']} |" in row, r["role_id"]
        assert f"({r['onet_soc_code']}) |" in row and r["onet_title"] in row, r["role_id"]
        assert "CC BY 4.0" in row, r["role_id"]


def test_new_roles_say_which_numbers_are_team_estimates():
    for r in get_roles()[8:]:
        assert "team estimates" in r["notes"], r["role_id"]
        assert r.get("skills_coverage") in (None, "limited"), r["role_id"]
        if r.get("skills_coverage") == "limited":
            assert "nothing is invented" in r["notes"] or "NOT yet populated" in r["notes"], r["role_id"]
    sdg = json.loads((ROOT / "data" / "sdg_mappings.json").read_text(encoding="utf-8"))
    new_rows = [m for m in sdg["role_sdg_mappings"] if m["role_id"] in ADDED_22]
    assert {m["role_id"] for m in new_rows} == set(ADDED_22)
    assert all(m["reason"].endswith("Team estimate.") for m in new_rows)


def test_every_sdg_row_points_at_a_real_role_or_skill():
    sdg = json.loads((ROOT / "data" / "sdg_mappings.json").read_text(encoding="utf-8"))
    role_ids = {r["role_id"] for r in get_roles()}
    for m in sdg["role_sdg_mappings"]:
        assert m["role_id"] in role_ids and 1 <= m["sdg_id"] <= 17, m
    for m in sdg["skill_sdg_mappings"]:
        assert m["skill_id"] in SKILLS and 1 <= m["sdg_id"] <= 17, m
    pairs = [(m["role_id"], m["sdg_id"]) for m in sdg["role_sdg_mappings"]]
    assert len(pairs) == len(set(pairs)), "duplicate role/SDG row"


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


def test_roles_per_industry_bucket():
    from collections import Counter
    assert Counter(r["industry_category"] for r in get_roles()[:8]) == {
        "Technology & AI": 2, "Business & Finance": 2,
        "Engineering & Manufacturing": 2, "Healthcare & Sustainability": 2,
    }
    assert Counter(r["industry_category"] for r in get_roles()) == {
        "Technology & AI": 9, "Business & Finance": 8,
        "Engineering & Manufacturing": 7, "Healthcare & Sustainability": 6,
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


def test_cv_aliases_resolve_and_never_collide():
    import re
    key = lambda s: re.sub(r"[^a-z0-9+#]", "", s.lower())  # same rule as Hussain's SkillNormalizer._key
    skills = json.loads((Path(__file__).resolve().parents[3] / "data" / "skills.json").read_text(encoding="utf-8"))["skills"]
    assert [s["skill_id"] for s in skills] == [
        "critical_thinking", "mathematics", "complex_problem_solving", "systems_analysis", "attention_to_detail",
        "excel", "sql", "python", "data_visualization", "cad_software", "matlab", "financial_analysis_software",
        "analytical_scientific_software", "vba", "programming", "javascript", "git", "accounting_software", "gis",
        "science",
    ]  # still the same 20 skills, same order
    owner = {}
    for s in skills:
        assert len(s["aliases"]) == len(set(s["aliases"])), s["skill_id"]
        for text in [s["skill_id"], s["name"], *s["aliases"]]:
            for k in (text.lower(), key(text)):
                assert owner.setdefault(k, s["skill_id"]) == s["skill_id"], (text, owner[k], s["skill_id"])
    for alias, skill_id in {
        "CAD": "cad_software", "QGIS": "gis", "Microsoft SQL Server": "sql",
        "MySQL": "sql", "PostgreSQL": "sql", "Advanced Excel": "excel",
    }.items():
        assert alias in next(s for s in skills if s["skill_id"] == skill_id)["aliases"], alias
        assert owner[key(alias)] == skill_id, alias


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
