"""Local handler tests: fake jobs, fake model, no RunPod and no sentence-transformers.

    python -m pytest runpod-worker -q
"""
import handler


class FakeModel:
    def __init__(self, dim=4):
        self.dim = dim
        self.calls = []

    def encode(self, texts, normalize_embeddings=False):
        self.calls.append((list(texts), normalize_embeddings))
        return [[float(len(t) + i) for i in range(self.dim)] for t in texts]


def run(job_input, model="default"):
    handler.set_model(FakeModel() if model == "default" else model)
    return handler.handler({"id": "test-job", "input": job_input})


def test_success_returns_embeddings_model_and_dim():
    out = run({"texts": ["SQL", "Data Visualization"]})
    assert out["model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert out["dim"] == 4
    assert len(out["embeddings"]) == 2 and all(len(v) == 4 for v in out["embeddings"])
    assert out["embeddings"][0] == [3.0, 4.0, 5.0, 6.0]
    assert "error" not in out


def test_model_is_asked_for_normalized_vectors_in_one_call():
    fake = FakeModel()
    run({"texts": ["a", "b", "c"]}, model=fake)
    assert fake.calls == [(["a", "b", "c"], True)]


def test_limits_are_inclusive():
    assert "embeddings" in run({"texts": ["x" * 200]})
    assert len(run({"texts": ["x"] * 256})["embeddings"]) == 256


def test_too_many_texts_rejected():
    out = run({"texts": ["x"] * 257})
    assert out == {"error": "too many texts: 257 (maximum 256)"}


def test_text_too_long_rejected_with_index():
    out = run({"texts": ["ok", "y" * 201]})
    assert out == {"error": "texts[1] is too long: 201 characters (maximum 200)"}


def test_bad_input_shapes_rejected():
    for bad in (None, [], "texts", {}, {"texts": "SQL"}, {"texts": []}, {"texts": [1]},
                {"texts": ["ok", None]}, {"texts": ["  "]}, {"texts": [""]}):
        out = run(bad)
        assert set(out) == {"error"}, bad
        assert out["error"]


def test_missing_input_key_in_job():
    handler.set_model(FakeModel())
    assert "error" in handler.handler({"id": "no-input"})
    assert "error" in handler.handler(None)


def test_invalid_input_never_reaches_the_model():
    fake = FakeModel()
    run({"texts": ["x"] * 300}, model=fake)
    assert fake.calls == []


def test_model_not_loaded_gives_clear_error():
    handler.set_model(None)
    assert handler.handler({"input": {"texts": ["SQL"]}}) == {"error": "model is not loaded"}
