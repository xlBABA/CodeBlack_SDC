"""Interpretation of unknown skill names via embeddings (all models are fakes; no network)."""
import json

import pytest

from services.matching import Matcher, SkillNormalizer
from services.matching.matcher import DEGRADED_CAVEAT
from services.matching.embeddings import DEFAULT_MODEL, EmbeddingProvider
from services.matching.normalizer import Interpretation
from services.matching.runpod_client import RunPodEmbeddingProvider
from services.matching.scoring import RELATED_CREDIT, SIMILARITY_THRESHOLD

SKILLS = [
    {"skill_id": "python", "name": "Python"},
    {"skill_id": "data_viz", "name": "Data Visualization", "aliases": ["Dashboards"]},
    {"skill_id": "customer_service", "name": "Customer Service"},
    {"skill_id": "customer_research", "name": "Customer Research"},
]
NOT_EQUIVALENT = [["customer_service", "customer_research"]]

VECTORS = {
    "Python": [0.0, 0.0, 1.0],
    "Data Visualization": [1.0, 0.0, 0.0],
    "Dashboards": [0.95, 0.3, 0.0],
    "Customer Service": [0.0, 1.0, 0.0],
    "Customer Research": [0.0, 0.95, 0.3],
    # free text typed by students
    "Charts and graphs": [1.0, 0.8, 0.0],   # 0.78 with the name, 0.93 with the alias Dashboards
    "Gardening": [0.3, 0.3, -0.9],          # below the threshold for every skill
    "Client work": [0.0, 1.0, 0.5],         # close to both customer skills
}

ROLE = {
    "role_id": "analyst",
    "role_title": "Analyst",
    "verified": True,
    "data_mode": "verified",
    "required_skills": [
        {"skill_id": "python", "importance": 1.0, "required": True},
        {"skill_id": "data_viz", "importance": 1.0, "required": True},
    ],
    "prerequisites": [],
}
OTHER_ROLE = {**ROLE, "role_id": "support", "role_title": "Support",
              "required_skills": [{"skill_id": "customer_service", "importance": 1.0, "required": True}]}

CAVEAT = ('Interpreted "Charts and graphs" as Data Visualization (similarity 0.93), '
          "partial credit; please confirm.")


class FakeModel:
    def __init__(self, fail_on_queries=False):
        self.calls = []
        self.fail_on_queries = fail_on_queries

    def encode(self, texts):
        self.calls.append(list(texts))
        if self.fail_on_queries and "Python" not in texts:  # catalogue embeds fine, queries fail
            raise RuntimeError("model down")
        return [VECTORS[t] for t in texts]


def provider(model=None, not_equivalent=NOT_EQUIVALENT):
    return EmbeddingProvider.from_skills(SKILLS, model=model or FakeModel(),
                                         not_equivalent=not_equivalent)


def student(*names):
    return {"skills": [{"name": n} for n in names], "semester": 4}


def run(similarity, *names, roles=(ROLE,)):
    return Matcher(SkillNormalizer(SKILLS), similarity).match_roles(
        student(*names), list(roles), limit=10)


# ---- provider.interpret ----

def test_maps_above_threshold_with_similarity():
    (hit,) = provider().interpret(["Charts and graphs"])
    assert hit[0] == "data_viz"
    assert hit[1] == pytest.approx(0.93, abs=0.005)  # best of name (0.78) and alias (0.93)
    assert hit[1] >= SIMILARITY_THRESHOLD


def test_rejects_below_threshold():
    assert provider().interpret(["Gardening"]) == [None]


def test_blank_text_is_none_and_not_embedded():
    model = FakeModel()
    assert provider(model).interpret(["", "   "]) == [None, None]
    assert [c for c in model.calls if "" in c or "   " in c] == []


def test_not_equivalent_candidates_make_a_text_ambiguous():
    assert provider().interpret(["Client work"]) == [None]
    # without the exclusion list the best candidate (Customer Research) is used
    hit = provider(not_equivalent=[]).interpret(["Client work"])[0]
    assert hit[0] == "customer_research"


def test_queries_are_batched_and_cached():
    model = FakeModel()
    p = provider(model)
    p.interpret(["Charts and graphs", "Gardening", "Charts and graphs"])
    p.interpret(["Gardening"])
    catalogue_calls = [c for c in model.calls if "Python" in c]
    query_calls = [c for c in model.calls if "Python" not in c]
    assert len(catalogue_calls) == 1
    assert query_calls == [["Charts and graphs", "Gardening"]]


# ---- normalizer + matcher ----

def test_interpreted_skill_gets_partial_credit():
    baseline = run(None, "Python")["matches"][0]
    with_interp = run(provider(), "Python", "Charts and graphs")["matches"][0]
    # Python at the default 0.85 factor; data_viz at 0.85 * RELATED_CREDIT
    assert baseline["score_breakdown"]["skills"] == round(100 * 0.85 / 2)
    assert with_interp["score_breakdown"]["skills"] == round(100 * (0.85 + 0.85 * RELATED_CREDIT) / 2)
    full = run(None, "Python", "Data Visualization")["matches"][0]
    assert baseline["score"] < with_interp["score"] < full["score"]


def test_caveat_on_matches_that_use_it_and_warning_in_response():
    data = run(provider(), "Python", "Charts and graphs", roles=(ROLE, OTHER_ROLE))
    by_id = {m["role_id"]: m for m in data["matches"]}
    assert CAVEAT in by_id["analyst"]["caveats"]
    assert CAVEAT not in by_id["support"]["caveats"]  # that role does not use the skill
    assert CAVEAT in data["warnings"]
    assert not any("not in the supported catalogue" in w for w in data["warnings"])


def test_interpreted_skill_is_reported_matched_and_not_counted_as_confirmed():
    match = run(provider(), "Python", "Charts and graphs")["matches"][0]
    assert {m["skill_id"] for m in match["matched_skills"]} == {"python", "data_viz"}
    assert match["missing_skills"] == []
    assert "1 of 2 core skills" in match["explanation"]
    assert "plus 1 interpreted" in match["explanation"]


def test_below_threshold_skill_is_dropped_with_the_usual_warning():
    data = run(provider(), "Python", "Gardening")
    assert any("'Gardening' is not in the supported catalogue" in w for w in data["warnings"])
    assert not any("Interpreted" in c for c in data["matches"][0]["caveats"])


def test_not_equivalent_text_is_dropped_with_the_usual_warning():
    data = run(provider(), "Python", "Client work", roles=(OTHER_ROLE,))
    assert any("'Client work' is not in the supported catalogue" in w for w in data["warnings"])


def test_confirmed_skill_beats_interpretation_and_needs_no_model_call():
    model = FakeModel()
    data = run(provider(model), "Python", "Data Visualization")
    assert all("Python" in call for call in model.calls)  # catalogue only, no query text
    assert not any("Interpreted" in w or "supported catalogue" in w for w in data["warnings"])


def test_exact_skill_wins_when_both_given():
    data = run(provider(), "Data Visualization", "Charts and graphs")
    assert not any("Interpreted" in w for w in data["warnings"])
    assert not any("Interpreted" in c for c in data["matches"][0]["caveats"])


def test_interpreted_skill_does_not_chain_into_related_credit():
    # data_viz is interpreted; the customer skills must not be credited through it
    sims = []

    class Spy(EmbeddingProvider):
        def __call__(self, a, b):
            sims.append((a, b))
            return super().__call__(a, b)

    spy = Spy({s["skill_id"]: [s["name"], *s.get("aliases", [])] for s in SKILLS}, model=FakeModel())
    run(spy, "Charts and graphs", roles=(OTHER_ROLE,))
    assert all(a != "data_viz" for a, _ in sims)


# ---- fallbacks ----

def test_no_provider_keeps_old_behaviour():
    data = run(None, "Python", "Charts and graphs")
    assert any("'Charts and graphs' is not in the supported catalogue" in w for w in data["warnings"])
    assert {m["skill_id"] for m in data["matches"][0]["matched_skills"]} == {"python"}


def test_plain_similarity_function_keeps_old_behaviour():
    data = run(lambda a, b: 0.0, "Python", "Charts and graphs")
    assert any("not in the supported catalogue" in w for w in data["warnings"])


def test_failing_provider_does_not_crash_and_keeps_old_behaviour():
    p = provider(FakeModel(fail_on_queries=True))
    data = run(p, "Python", "Charts and graphs")
    assert any("'Charts and graphs' is not in the supported catalogue" in w for w in data["warnings"])
    assert data["matches"][0]["score_breakdown"]["skills"] == round(100 * 0.85 / 2)
    assert all(DEGRADED_CAVEAT in m["caveats"] for m in data["matches"])


def test_no_degraded_caveat_when_nothing_needed_interpreting_or_it_worked():
    p = provider(FakeModel(fail_on_queries=True))
    assert all(DEGRADED_CAVEAT not in m["caveats"] for m in run(p, "Python")["matches"])  # no unknown skills
    assert all(DEGRADED_CAVEAT not in m["caveats"] for m in run(provider(), "Charts and graphs")["matches"])


def test_adapter_adds_the_degraded_caveat_once_when_interpretation_fails():
    from services.matching.backend_adapter import HussainMatchingProvider
    adapter = HussainMatchingProvider(similarity=provider(FakeModel(fail_on_queries=True)),
                                      skills_catalogue=SKILLS)
    role = {"role_id": "analyst", "role_title": "Analyst",
            "required_skills": [{"skill_id": "python", "weight": 1.0}, {"skill_id": "data_viz", "weight": 1.0}]}
    (match,) = adapter.match(student("Python", "Charts and graphs"), [role], None, [])
    assert match["caveats"].count(DEGRADED_CAVEAT) == 1


def test_interpreter_with_wrong_result_count_is_ignored():
    normalizer = SkillNormalizer(SKILLS)
    resolved, warnings, interpreted = normalizer.interpret_profile_skills(
        [{"name": "Charts and graphs"}], lambda names: [])
    assert resolved == {} and interpreted == {}
    assert len(warnings) == 1 and "not in the supported catalogue" in warnings[0]


def test_old_normalize_profile_skills_is_unchanged():
    resolved, warnings = SkillNormalizer(SKILLS).normalize_profile_skills(
        [{"name": "python"}, {"name": "Charts and graphs"}])
    assert resolved == {"python": None}
    assert len(warnings) == 1


def test_interpretation_message_format():
    msg = Interpretation("Charts and graphs", "data_viz", "Data Visualization", 0.62).message()
    assert msg == ('Interpreted "Charts and graphs" as Data Visualization (similarity 0.62), '
                   "partial credit; please confirm.")


# ---- RunPod provider (HTTP mocked) ----

class FakeResponse:
    def __init__(self, body):
        self._body = json.dumps(body).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_runpod_provider_interprets_free_text():
    requests = []

    def opener(request, timeout=None):
        texts = json.loads(request.data)["input"]["texts"]
        requests.append(texts)
        vectors = [VECTORS[t] for t in texts]
        return FakeResponse({"status": "COMPLETED", "output": {
            "embeddings": vectors, "model": DEFAULT_MODEL, "dim": 3}})

    p = RunPodEmbeddingProvider.from_skills(
        SKILLS, api_key="k", endpoint_id="ep", opener=opener, not_equivalent=NOT_EQUIVALENT)
    data = run(p, "Python", "Charts and graphs")
    assert CAVEAT in data["matches"][0]["caveats"]
    assert requests[-1] == ["Charts and graphs"]


def test_runpod_failure_falls_back_without_crashing():
    def opener(request, timeout=None):
        texts = json.loads(request.data)["input"]["texts"]
        if "Python" not in texts:  # the catalogue embeds, the query call times out
            raise TimeoutError()
        return FakeResponse({"status": "COMPLETED", "output": {
            "embeddings": [VECTORS[t] for t in texts], "model": DEFAULT_MODEL, "dim": 3}})

    p = RunPodEmbeddingProvider.from_skills(SKILLS, api_key="k", endpoint_id="ep",
                                            opener=opener, retries=0)
    data = run(p, "Python", "Charts and graphs")
    assert any("not in the supported catalogue" in w for w in data["warnings"])
    assert all(DEGRADED_CAVEAT in m["caveats"] for m in data["matches"])
