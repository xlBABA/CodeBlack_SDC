# Vendored from origin/feature/hussain-matching @ 61373a5 (owner: Hussain), source
# services/matching/tests/test_embeddings.py, with import paths rewritten to this package location.
"""EmbeddingProvider tests.

Fake-model tests always run. Real-model tests (synonyms vs unrelated pairs) skip
when sentence-transformers is not installed, so the other tests are unaffected.
"""
import json
from pathlib import Path

import pytest

from app.services.hussain_matching import Matcher, SkillNormalizer
from app.services.hussain_matching.embeddings import EmbeddingProvider
from app.services.hussain_matching.scoring import SIMILARITY_THRESHOLD

SKILLS = [
    {"skill_id": "data_viz", "name": "Data Visualization"},
    {"skill_id": "dashboards", "name": "Dashboards"},
    {"skill_id": "machine_learning", "name": "Machine Learning"},
    {"skill_id": "ml", "name": "ML Modeling"},
    {"skill_id": "cooking", "name": "Cooking"},
    {"skill_id": "welding", "name": "Welding"},
]

# (a, b) pairs that mean nearly the same thing / nothing alike
SYNONYM_PAIRS = [("data_viz", "dashboards"), ("machine_learning", "ml")]
UNRELATED_PAIRS = [("data_viz", "cooking"), ("machine_learning", "welding"), ("dashboards", "cooking")]


class FakeModel:
    """Deterministic 3-d vectors; counts encode calls and texts."""

    VECTORS = {
        "Data Visualization": [1.0, 0.1, 0.0],
        "Dashboards": [0.9, 0.2, 0.0],
        "Machine Learning": [0.0, 1.0, 0.1],
        "ML Modeling": [0.0, 0.9, 0.2],
        "Cooking": [0.0, 0.0, 1.0],
        "Welding": [0.1, 0.0, 0.9],
    }

    def __init__(self):
        self.calls = []

    def encode(self, texts):
        self.calls.append(list(texts))
        return [self.VECTORS[t] for t in texts]


# ---- fake-model tests (no dependency needed) ----

def test_similarity_is_cosine_and_symmetric():
    p = EmbeddingProvider.from_skills(SKILLS, model=FakeModel())
    assert p("data_viz", "data_viz") == pytest.approx(1.0)
    assert p("data_viz", "dashboards") == pytest.approx(p("dashboards", "data_viz"))
    assert p("data_viz", "dashboards") > p("data_viz", "cooking")


def test_embeddings_are_precomputed_once_in_one_batch():
    model = FakeModel()
    p = EmbeddingProvider.from_skills(SKILLS, model=model)
    p("data_viz", "dashboards")
    p("ml", "cooking")
    p("welding", "data_viz")
    assert len(model.calls) == 1
    assert sorted(model.calls[0]) == sorted(s["name"] for s in SKILLS)


def test_unknown_skill_id_scores_zero_without_loading_model():
    model = FakeModel()
    p = EmbeddingProvider.from_skills(SKILLS, model=model)
    assert p("data_viz", "not_a_skill") == 0.0
    assert model.calls == []


def test_disk_cache_is_reused_and_invalidated(tmp_path):
    cache = tmp_path / "emb.json"
    first = FakeModel()
    EmbeddingProvider.from_skills(SKILLS, model=first, cache_path=cache)("data_viz", "cooking")
    assert cache.exists() and len(first.calls) == 1

    second = FakeModel()
    p = EmbeddingProvider.from_skills(SKILLS, model=second, cache_path=cache)
    assert p("data_viz", "dashboards") > 0.9
    assert second.calls == []  # fully served from cache

    third = FakeModel()
    renamed = [dict(s, name="Cooking") if s["skill_id"] == "cooking" else s for s in SKILLS]
    renamed[4]["name"] = "Welding"  # name changed -> only that skill is re-embedded
    EmbeddingProvider.from_skills(renamed, model=third, cache_path=cache)("cooking", "welding")
    assert third.calls == [["Welding"]]

    other_model = FakeModel()
    p = EmbeddingProvider.from_skills(SKILLS, model_name="other/model", model=other_model, cache_path=cache)
    p("data_viz", "cooking")
    assert len(other_model.calls) == 1  # different model name -> cache ignored


def test_corrupt_cache_is_ignored(tmp_path):
    cache = tmp_path / "emb.json"
    cache.write_text("{not json")
    p = EmbeddingProvider.from_skills(SKILLS, model=FakeModel(), cache_path=cache)
    assert p("data_viz", "dashboards") > 0.9


def test_plugs_into_matcher_for_partial_credit(normalizer, roles):
    """A provider as the similarity hook gives partial credit, never full credit."""
    names = {s["skill_id"]: s["name"] for s in normalizer._by_id.values()}
    role = roles[0]
    needed = role["required_skills"][0]["skill_id"]
    other = next(sid for sid in names if sid != needed)

    class Pairwise(FakeModel):
        def encode(self, texts):  # `other` and `needed` share a direction, rest orthogonal-ish
            return [[1.0, 0.0] if t in (names[needed], names[other]) else [0.0, 1.0] for t in texts]

    provider = EmbeddingProvider(names, model=Pairwise())
    assert provider(needed, other) == pytest.approx(1.0)
    profile = {"skills": [{"skill_id": other}]}
    base = Matcher(normalizer).match_roles(profile, [role])["matches"][0]
    smart = Matcher(normalizer, similarity=provider).match_roles(profile, [role])["matches"][0]
    assert smart["score_breakdown"]["skills"] > base["score_breakdown"]["skills"]
    assert any(m["skill_id"] == needed for m in smart["missing_skills"])  # gap stays listed


def test_missing_library_gives_clear_error(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "sentence_transformers":
            raise ImportError("blocked")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="pip install sentence-transformers"):
        EmbeddingProvider.from_skills(SKILLS)("data_viz", "dashboards")


# ---- name + alias texts, max cosine (no model needed) ----

def test_skill_texts_are_name_then_aliases():
    from app.services.hussain_matching.embeddings import skill_texts

    assert skill_texts({"name": "Data Visualization", "aliases": ["Data Viz", "Dashboards"]}) == [
        "Data Visualization", "Data Viz", "Dashboards"
    ]
    assert skill_texts({"name": "Cooking"}) == ["Cooking"]


def test_name_and_each_alias_are_embedded_separately_in_one_batch():
    model = FakeModel()
    model.VECTORS = {"Cooking": [0.0, 0.0, 1.0], "Culinary Arts": [0.0, 0.1, 0.9], "Welding": [0.1, 0.0, 0.9]}
    skills = [{"skill_id": "cooking", "name": "Cooking", "aliases": ["Culinary Arts"]}, SKILLS[5]]
    EmbeddingProvider.from_skills(skills, model=model)("cooking", "welding")
    assert len(model.calls) == 1
    assert sorted(model.calls[0]) == ["Cooking", "Culinary Arts", "Welding"]


def test_similarity_is_max_over_all_text_pairs():
    model = FakeModel()
    model.VECTORS = {
        "Alpha": [1.0, 0.0], "Alpha alias": [0.0, 1.0],
        "Beta": [1.0, 0.0], "Gamma": [0.0, 1.0],
    }
    skills = [
        {"skill_id": "a", "name": "Alpha", "aliases": ["Alpha alias"]},
        {"skill_id": "b", "name": "Beta"},
        {"skill_id": "g", "name": "Gamma"},
    ]
    p = EmbeddingProvider.from_skills(skills, model=model)
    assert p("a", "b") == pytest.approx(1.0)  # name matches Beta
    assert p("a", "g") == pytest.approx(1.0)  # alias matches Gamma
    assert p("b", "g") == pytest.approx(0.0)


def test_alias_change_reembeds_only_that_skill(tmp_path):
    cache = tmp_path / "emb.json"
    model = FakeModel()
    model.VECTORS = {"Cooking": [0, 0, 1.0], "Culinary Arts": [0, 0.1, 0.9], "Baking": [0, 0.2, 0.8], "Welding": [0.1, 0, 0.9]}
    skills = [{"skill_id": "cooking", "name": "Cooking", "aliases": ["Culinary Arts"]}, SKILLS[5]]
    EmbeddingProvider.from_skills(skills, model=model, cache_path=cache)("cooking", "welding")

    changed = FakeModel()
    changed.VECTORS = model.VECTORS
    skills[0] = {"skill_id": "cooking", "name": "Cooking", "aliases": ["Baking"]}
    EmbeddingProvider.from_skills(skills, model=changed, cache_path=cache)("cooking", "welding")
    assert sorted(changed.calls[0]) == ["Baking", "Cooking"]  # welding came from cache


# ---- not_equivalent exclusion list ----

FIXTURE_CATALOGUE = json.loads(
    (Path(__file__).resolve().parent.parent / "fixtures" / "skills_fixture.json").read_text(encoding="utf-8")
)


def test_not_equivalent_pairs_return_zero_in_both_orders_without_loading_model():
    model = FakeModel()
    p = EmbeddingProvider.from_skills(SKILLS, model=model, not_equivalent=[["data_viz", "dashboards"]])
    assert p("data_viz", "dashboards") == 0.0
    assert p("dashboards", "data_viz") == 0.0
    assert model.calls == []
    assert p("machine_learning", "ml") > 0.9


def test_not_equivalent_only_blocks_the_listed_pair():
    p = EmbeddingProvider.from_skills(SKILLS, model=FakeModel(), not_equivalent=[["data_viz", "dashboards"]])
    unblocked = EmbeddingProvider.from_skills(SKILLS, model=FakeModel())
    assert unblocked("data_viz", "dashboards") > 0.9
    assert p("data_viz", "data_viz") == pytest.approx(1.0)
    assert p("dashboards", "cooking") == pytest.approx(unblocked("dashboards", "cooking"))


@pytest.mark.parametrize("bad", [["data_viz"], ["data_viz", "data_viz"], ["data_viz", "nope"], ["a", "b", "c"]])
def test_not_equivalent_rejects_malformed_or_unknown_entries(bad):
    with pytest.raises(ValueError):
        EmbeddingProvider.from_skills(SKILLS, model=FakeModel(), not_equivalent=[bad])


def test_fixture_catalogue_lists_the_example_pairs_with_valid_ids():
    ids = {s["skill_id"] for s in FIXTURE_CATALOGUE["skills"]}
    pairs = {frozenset(p) for p in FIXTURE_CATALOGUE["not_equivalent"]}
    assert pairs == {
        frozenset(("customer_service", "customer_research")),
        frozenset(("sales", "marketing")),
        frozenset(("java", "javascript")),
    }
    assert all(i in ids for pair in pairs for i in pair)
    SkillNormalizer(FIXTURE_CATALOGUE["skills"])  # catalogue still loads (no alias clashes)


def test_from_catalogue_applies_the_exclusion_list():
    class Model:
        def encode(self, texts):
            return [[1.0, 0.0] for _ in texts]  # every text identical -> cosine 1.0

    p = EmbeddingProvider.from_catalogue(FIXTURE_CATALOGUE, model=Model())
    assert p("sales", "marketing") == 0.0
    assert p("java", "javascript") == 0.0
    assert p("customer_service", "customer_research") == 0.0
    assert p("sales", "java") == pytest.approx(1.0)


def test_threshold_matches_calibration_choice():
    assert SIMILARITY_THRESHOLD == 0.60


# ---- real model tests (skip without sentence-transformers) ----
# Name and aliases are embedded separately (max cosine). Scores measured with
# all-MiniLM-L6-v2: synonyms 0.83 to 0.92, unrelated pairs under 0.35.

REAL_SKILLS = [
    {"skill_id": "viz", "name": "Data Visualization", "aliases": ["Data Viz", "Dashboards"]},
    {"skill_id": "dash", "name": "Dashboard Design", "aliases": ["BI Dashboards", "Dashboard Building"]},
    {"skill_id": "sql", "name": "SQL", "aliases": ["Structured Query Language"]},
    {"skill_id": "dbq", "name": "Database Querying", "aliases": ["SQL queries", "Relational Databases"]},
    {"skill_id": "team", "name": "Teamwork", "aliases": ["Collaboration"]},
    {"skill_id": "tc", "name": "Team Collaboration", "aliases": ["Working in Teams", "Group Work"]},
    {"skill_id": "ml", "name": "Machine Learning", "aliases": ["ML", "Predictive Modeling"]},
    {"skill_id": "mlm", "name": "ML Modeling", "aliases": ["Machine Learning Models", "Statistical Modeling"]},
    {"skill_id": "cook", "name": "Cooking", "aliases": ["Culinary Arts"]},
    {"skill_id": "weld", "name": "Welding", "aliases": ["Metal Fabrication"]},
    {"skill_id": "tax", "name": "Tax Accounting", "aliases": ["Bookkeeping"]},
]
REAL_SYNONYMS = [("viz", "dash"), ("sql", "dbq"), ("team", "tc"), ("ml", "mlm")]
REAL_UNRELATED = [("viz", "cook"), ("sql", "weld"), ("team", "weld"), ("ml", "cook"), ("dash", "tax")]


@pytest.fixture(scope="module")
def real_provider():
    pytest.importorskip("sentence_transformers")
    return EmbeddingProvider.from_skills(REAL_SKILLS)


@pytest.mark.parametrize("a,b", REAL_SYNONYMS)
def test_real_model_synonyms_are_close(real_provider, a, b):
    assert real_provider(a, b) >= 0.55


@pytest.mark.parametrize("a,b", REAL_UNRELATED)
def test_real_model_unrelated_pairs_are_far(real_provider, a, b):
    assert real_provider(a, b) < 0.4


def test_real_model_synonyms_beat_unrelated(real_provider):
    closest_unrelated = max(real_provider(a, b) for a, b in REAL_UNRELATED)
    for a, b in REAL_SYNONYMS:
        assert real_provider(a, b) > closest_unrelated + 0.2


def test_real_model_aliases_raise_a_related_pair(real_provider):
    """'Data Visualization' vs 'Dashboard Design': names alone score about 0.40;
    with aliases (max over text pairs) the pair scores clearly higher."""
    names_only = EmbeddingProvider({s["skill_id"]: s["name"] for s in REAL_SKILLS})
    assert real_provider("viz", "dash") > names_only("viz", "dash") + 0.2


def test_real_model_exclusions_block_pairs_that_would_pass_the_threshold(real_provider):
    plain = EmbeddingProvider.from_catalogue(
        {"skills": FIXTURE_CATALOGUE["skills"]}
    )
    blocked = EmbeddingProvider.from_catalogue(FIXTURE_CATALOGUE)
    for a, b in [("customer_service", "customer_research"), ("sales", "marketing")]:
        assert plain(a, b) >= SIMILARITY_THRESHOLD  # without the list these would get credit
        assert blocked(a, b) == 0.0
    assert plain("java", "javascript") > 0.3  # related, but below the threshold anyway
    assert blocked("java", "javascript") == 0.0
