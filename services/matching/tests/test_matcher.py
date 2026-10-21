import pytest

from services.matching import Matcher, get_scenario, match

ROLE_MATCH_KEYS = {
    "role_id", "role_title", "score", "score_type", "matched_skills", "missing_skills",
    "score_breakdown", "evidence_ids", "explanation", "caveats",
}
BREAKDOWN_KEYS = {"skills", "experience", "prerequisites", "transferable"}


def test_output_follows_contract(matcher, cs_student, roles):
    data = matcher.match_roles(cs_student, roles, scenario_id="moderate")
    assert set(data) >= {"matches", "catalog_coverage", "methodology_version"}
    assert data["catalog_coverage"] == {"verified": 4, "total_target": 30}
    for m in data["matches"]:
        assert set(m) == ROLE_MATCH_KEYS
        assert set(m["score_breakdown"]) == BREAKDOWN_KEYS
        assert m["score_type"] == "profile_alignment_estimate"
        assert isinstance(m["score"], int) and 0 <= m["score"] <= 100
        assert "not a hiring prediction" in m["explanation"]


def test_cs_student_ranks_data_analyst_first(matcher, cs_student, roles):
    top = matcher.match_roles(cs_student, roles)["matches"][0]
    assert top["role_id"] == "data_analyst"
    assert {s["skill_id"] for s in top["matched_skills"]} == {"python", "sql"}
    assert {"data_visualization", "statistics"} <= {s["skill_id"] for s in top["missing_skills"]}


def test_business_student_ranks_business_analyst_first(matcher, business_student, roles):
    top = matcher.match_roles(business_student, roles)["matches"][0]
    assert top["role_id"] == "business_analyst"
    assert top["score_breakdown"]["experience"] > 0  # project mentions Excel


def test_scoring_is_deterministic(matcher, cs_student, roles):
    assert matcher.match_roles(cs_student, roles) == matcher.match_roles(cs_student, roles)


def test_empty_profile_scores_low_and_warns(matcher, roles):
    data = matcher.match_roles({"skills": []}, roles)
    assert all(m["score_breakdown"]["skills"] == 0 for m in data["matches"])
    assert any("No recognised skills" in w for w in data["warnings"])


def test_full_skill_profile_gets_full_coverage(matcher, roles):
    da = next(r for r in roles if r["role_id"] == "data_analyst")
    profile = {"skills": [{"skill_id": r["skill_id"], "proficiency": "advanced"} for r in da["required_skills"]]}
    m = next(m for m in matcher.match_roles(profile, roles)["matches"] if m["role_id"] == "data_analyst")
    assert m["score_breakdown"]["skills"] == 100 and m["missing_skills"] == []


def test_unverified_roles_are_never_ranked(matcher, cs_student, roles):
    roles.append({**roles[0], "role_id": "made_up_role", "verified": False})
    ids = [m["role_id"] for m in matcher.match_roles(cs_student, roles)["matches"]]
    assert "made_up_role" not in ids


def test_limit_and_low_coverage_warning(matcher, cs_student, roles):
    data = matcher.match_roles(cs_student, roles, limit=2)
    assert len(data["matches"]) == 2
    data = matcher.match_roles(cs_student, roles, limit=6)
    assert len(data["matches"]) == 4
    assert any("Only 4 verified roles" in w for w in data["warnings"])


def test_duplicate_role_ids_rejected(matcher, cs_student, roles):
    roles.append(dict(roles[0]))
    with pytest.raises(ValueError, match="Duplicate role_id"):
        matcher.match_roles(cs_student, roles)


def test_missing_prerequisite_info_is_a_caveat(matcher, roles):
    m = matcher.match_roles({"skills": [{"name": "SQL"}]}, roles)["matches"][0]
    assert m["score_breakdown"]["prerequisites"] == 50
    assert any(c.startswith("Not provided") for c in m["caveats"])


# ---- scenarios and trend signals ----

SQL_RISING = [{"signal_id": "sig1", "skill_id": "sql", "source_id": "fixture_src_1", "direction": "rising"}]
VIZ_RISING = [{"signal_id": "sig2", "skill_id": "data_visualization", "source_id": "fixture_src_2", "direction": "rising"}]


def _score(matcher, profile, roles, role_id, scenario, signals):
    data = matcher.match_roles(profile, roles, scenario_id=scenario, signals=signals)
    return next(m for m in data["matches"] if m["role_id"] == role_id)


def test_no_signals_means_scenarios_do_not_change_scores(matcher, cs_student, roles):
    mod = _score(matcher, cs_student, roles, "data_analyst", "moderate", [])
    fast = _score(matcher, cs_student, roles, "data_analyst", "fast", [])
    assert mod["score"] == fast["score"]
    assert any("No dated trend signals" in c for c in mod["caveats"])


def test_rising_held_skill_raises_score_more_in_fast(matcher, cs_student, roles):
    base = _score(matcher, cs_student, roles, "data_analyst", None, None)["score_breakdown"]["skills"]
    mod = _score(matcher, cs_student, roles, "data_analyst", "moderate", SQL_RISING)
    fast = _score(matcher, cs_student, roles, "data_analyst", "fast", SQL_RISING)
    assert base < mod["score_breakdown"]["skills"] < fast["score_breakdown"]["skills"]
    assert "fixture_src_1" in fast["evidence_ids"]
    assert any("Scenario adjusted" in c for c in fast["caveats"])


def test_rising_missing_skill_lowers_score(matcher, cs_student, roles):
    base = _score(matcher, cs_student, roles, "data_analyst", None, None)["score_breakdown"]["skills"]
    fast = _score(matcher, cs_student, roles, "data_analyst", "fast", VIZ_RISING)["score_breakdown"]["skills"]
    assert fast < base


def test_scenario_influence_is_bounded(matcher, cs_student, roles):
    base = _score(matcher, cs_student, roles, "data_analyst", None, None)["score"]
    fast = _score(matcher, cs_student, roles, "data_analyst", "fast", SQL_RISING)["score"]
    assert abs(fast - base) <= 10


def test_conflicting_signals_are_ignored(matcher, cs_student, roles):
    signals = SQL_RISING + [{"signal_id": "sig3", "skill_id": "sql", "source_id": "x", "direction": "falling"}]
    base = _score(matcher, cs_student, roles, "data_analyst", None, None)["score"]
    m = _score(matcher, cs_student, roles, "data_analyst", "fast", signals)
    assert m["score"] == base and any("Conflicting" in c for c in m["caveats"])


def test_unknown_scenario_raises(matcher, cs_student, roles):
    with pytest.raises(ValueError, match="Unknown scenario_id"):
        matcher.match_roles(cs_student, roles, scenario_id="apocalypse", signals=SQL_RISING)


def test_get_scenario_has_assumptions_and_uncertainty():
    s = get_scenario("fast")
    assert s["assumptions"] and "not predictions" in s["uncertainty_note"]


# ---- embedding similarity hook (RunPod plugs in here later) ----

def test_similarity_gives_partial_credit_only(normalizer, roles):
    profile = {"skills": [{"name": "Excel"}]}

    def fake_similarity(a, b):
        return 0.9 if {a, b} == {"excel", "data_visualization"} else 0.0

    plain = Matcher(normalizer).match_roles(profile, roles)
    smart = Matcher(normalizer, similarity=fake_similarity).match_roles(profile, roles)
    p = next(m for m in plain["matches"] if m["role_id"] == "data_analyst")
    s = next(m for m in smart["matches"] if m["role_id"] == "data_analyst")
    assert s["score_breakdown"]["skills"] > p["score_breakdown"]["skills"]
    assert "data_visualization" in {x["skill_id"] for x in s["missing_skills"]}  # still a gap
    assert any("related to Data Visualization" in c for c in s["caveats"])


def test_adapter_function_returns_role_matches(normalizer, cs_student, roles):
    result = match(cs_student, roles, "moderate", [], normalizer=normalizer)
    assert isinstance(result, list) and result[0]["role_id"] == "data_analyst"
