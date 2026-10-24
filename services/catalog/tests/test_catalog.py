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


def _git_roles(commit):
    return subprocess.run(["git", "show", f"{commit}:data/roles.json"],
                          cwd=ROOT, capture_output=True, check=True).stdout.replace(b"\r\n", b"\n")


def _record_bytes(text, role_id):
    """The exact text of one role record ("  {" ... "  }") in roles.json."""
    start = text.index(b'    "role_id": "%s",' % role_id.encode()) - len(b"  {\n")
    return text[start: text.index(b"\n  }", start) + len(b"\n  }")]


# Approved exception: public_health_analyst was rebuilt on 2026-10-24 with the 22-role
# O*NET rule ("Option C", approved by Rehan and Hussain), so it is no longer byte-identical.
APPROVED_REBUILDS = {"public_health_analyst"}


def test_first_eight_roles_are_byte_identical_to_the_base():
    # base = feat/jawad-data-fixes @ 9817054, where the 8 original roles were last changed
    base = _git_roles("98170543e1210c57d21d3f19d96ab44247810ea1")
    now = (ROOT / "data" / "roles.json").read_bytes().replace(b"\r\n", b"\n")
    assert [r["role_id"] for r in json.loads(now)[:8]] == [r["role_id"] for r in json.loads(base)]
    for r in json.loads(base):
        if r["role_id"] in APPROVED_REBUILDS:
            continue
        assert _record_bytes(now, r["role_id"]) == _record_bytes(base, r["role_id"]), r["role_id"]
    assert {r["role_id"] for r in json.loads(base)} - APPROVED_REBUILDS == set(ORIGINAL_4 + ADDED_4) - {"public_health_analyst"}


def test_public_health_analyst_rebuilt_with_the_22_role_rule():
    ph = get_role("public_health_analyst")
    got = {s["skill_id"]: (s["importance"], s["required"]) for s in ph["required_skills"]}
    # O*NET 19-1041.00 Details, fetched 2026-10-24: every catalog cognitive skill scoring 50 or more
    onet_ge50 = {"critical_thinking": 81, "complex_problem_solving": 81, "science": 78, "systems_analysis": 75, "mathematics": 69}
    bucket = lambda x: 5 if x >= 70 else 4 if x >= 60 else 3
    for sid, score in onet_ge50.items():
        assert got.get(sid) == (bucket(score), True), sid  # present, bucket-derived, required (bucket >= 4)
    assert {"complex_problem_solving", "science", "systems_analysis"} <= set(got)
    assert "attention_to_detail" not in got and "programming" not in got  # Work Style 90; Programming 16
    assert got["python"][1] is False and got["sql"][1] is False
    assert ph["skills_coverage"] == "limited" and "Biology (82)" in ph["notes"] and "team estimates" in ph["notes"]


def test_every_other_role_record_is_unchanged_since_7c17db1():
    base = _git_roles("7c17db1794c4ae7d196f739eaf0dda6aa552d6c7")
    now = (ROOT / "data" / "roles.json").read_bytes().replace(b"\r\n", b"\n")
    ids = [r["role_id"] for r in json.loads(base)]
    assert ids == [r["role_id"] for r in json.loads(now)]
    for rid in ids:
        if rid not in APPROVED_REBUILDS:
            assert _record_bytes(now, rid) == _record_bytes(base, rid), rid


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


ORIGINAL_12_PAIRS = [
    ["python", "javascript"], ["python", "matlab"], ["excel", "vba"], ["excel", "accounting_software"],
    ["accounting_software", "financial_analysis_software"], ["critical_thinking", "complex_problem_solving"],
    ["complex_problem_solving", "systems_analysis"], ["mathematics", "science"], ["git", "programming"],
    ["cad_software", "gis"], ["data_visualization", "gis"], ["matlab", "analytical_scientific_software"],
]
NEW_PAIRS = [["git", "gis"], ["financial_analysis_software", "analytical_scientific_software"]]  # Hussain: 0.74 and 0.67


def test_fourteen_not_equivalent_pairs_with_reasons():
    root = Path(__file__).resolve().parents[3]
    pairs = json.loads((root / "data" / "skill_not_equivalent.json").read_text(encoding="utf-8"))["not_equivalent"]
    assert len(pairs) == 14
    assert pairs[:12] == ORIGINAL_12_PAIRS  # the original 12 unchanged, in order
    assert pairs[12:] == NEW_PAIRS
    unordered = [frozenset(p) for p in pairs]
    assert len(set(unordered)) == 14, "duplicate pair (a/b and b/a count as the same)"
    assert all(len(p) == 2 and p[0] != p[1] and set(p) <= set(SKILLS) for p in pairs)
    assert not set(unordered) & {frozenset(["programming", "python"]), frozenset(["programming", "javascript"])}
    register = (root / "docs" / "source-register.md").read_text(encoding="utf-8")
    for a, b in pairs:
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
