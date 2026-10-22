# Vendored from origin/feature/hussain-matching @ 61373a5 (owner: Hussain), source
# services/matching/tests/test_runpod_client.py, with import paths rewritten to this package location
# (including the monkeypatch.setattr target string below).
"""RunPod client and adapter fallback tests. All HTTP is mocked; nothing touches the network."""
import io
import json
import logging
import urllib.error
import urllib.request

import pytest

from app.services.hussain_matching import runpod_client
from app.services.hussain_matching.backend_adapter import DEGRADED_CAVEAT, HussainMatchingProvider
from app.services.hussain_matching.runpod_client import (
    RunPodConfigError, RunPodEmbeddingProvider, RunPodError, runpod_configured,
)

KEY = "rpa_SECRET_KEY_123"
ENDPOINT = "abc123xyz"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SKILLS = [
    {"skill_id": "sales", "name": "Sales", "aliases": []},
    {"skill_id": "marketing", "name": "Marketing", "aliases": []},
    {"skill_id": "welding", "name": "Welding", "aliases": []},
]
VECTORS = {"Sales": [1.0, 0.0, 0.0], "Marketing": [0.95, 0.31, 0.0], "Welding": [0.0, 0.0, 1.0]}


class FakeResponse:
    def __init__(self, body):
        self._raw = body if isinstance(body, bytes) else json.dumps(body).encode()

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def completed(embeddings, dim=None):
    return {"status": "COMPLETED", "output": {
        "embeddings": embeddings, "model": MODEL, "dim": dim or len(embeddings[0])}}


def ok_body(texts):
    return completed([VECTORS[t] for t in texts])


def same_vector_for_everything(texts):
    return completed([[1.0, 0.0]] * len(texts))


class FakeOpener:
    """Plays a script. Each step is an exception to raise, a body to return, or a
    callable(texts) -> body. The last step repeats."""

    def __init__(self, *script):
        self.script = list(script)
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        if isinstance(step, BaseException):
            raise step
        texts = json.loads(request.data)["input"]["texts"]
        return FakeResponse(step(texts) if callable(step) else step)


def http_error(code):
    return urllib.error.HTTPError("https://api.runpod.ai/x", code, "err", {}, io.BytesIO(b""))


def provider(opener, **kw):
    return RunPodEmbeddingProvider.from_skills(SKILLS, api_key=KEY, endpoint_id=ENDPOINT, opener=opener, **kw)


# ---- success ----

def test_success_request_shape_and_similarity():
    opener = FakeOpener(ok_body)
    p = provider(opener, timeout=12)
    assert p("sales", "marketing") == pytest.approx(0.95 / (0.95**2 + 0.31**2) ** 0.5, abs=1e-6)
    assert p("sales", "welding") == pytest.approx(0.0)
    assert len(opener.requests) == 1  # one batch, then cached in memory
    req = opener.requests[0]
    assert req.full_url == f"https://api.runpod.ai/v2/{ENDPOINT}/runsync"
    assert req.get_method() == "POST"
    assert req.get_header("Authorization") == f"Bearer {KEY}"
    assert json.loads(req.data) == {"input": {"texts": ["Sales", "Marketing", "Welding"]}}
    assert opener.timeouts == [12]


def test_not_equivalent_is_respected_without_a_request():
    opener = FakeOpener(ok_body)
    p = provider(opener, not_equivalent=[["sales", "marketing"]])
    assert p("sales", "marketing") == 0.0 and p("marketing", "sales") == 0.0
    assert opener.requests == []
    assert p("sales", "welding") == pytest.approx(0.0)  # other pairs still use the endpoint
    assert len(opener.requests) == 1


def test_aliases_are_sent_as_separate_texts():
    seen = []

    def body(texts):
        seen.append(texts)
        return same_vector_for_everything(texts)

    p = RunPodEmbeddingProvider.from_skills(
        [{"skill_id": "a", "name": "A", "aliases": ["A1", "A2"]}],
        api_key=KEY, endpoint_id=ENDPOINT, opener=FakeOpener(body))
    p.precompute()
    assert seen == [["A", "A1", "A2"]]


def test_large_catalogues_are_batched_and_long_texts_truncated():
    seen = []

    def body(texts):
        seen.append(texts)
        return same_vector_for_everything(texts)

    skills = [{"skill_id": f"s{i}", "name": f"Skill {i}"} for i in range(300)]
    skills[0]["name"] = "x" * 500
    RunPodEmbeddingProvider.from_skills(
        skills, api_key=KEY, endpoint_id=ENDPOINT, opener=FakeOpener(body)).precompute()
    assert [len(b) for b in seen] == [256, 44]
    assert len(seen[0][0]) == 200


def test_disk_cache_avoids_a_second_request(tmp_path):
    cache = tmp_path / "emb.json"
    provider(FakeOpener(ok_body), cache_path=cache)("sales", "welding")
    again = FakeOpener(RuntimeError("must not be called"))
    assert provider(again, cache_path=cache)("sales", "marketing") > 0.9
    assert again.requests == []


# ---- timeout, retry, transient errors ----

def test_timeout_is_retried_once_then_succeeds():
    opener = FakeOpener(TimeoutError("slow"), ok_body)
    assert provider(opener)("sales", "welding") == pytest.approx(0.0)
    assert len(opener.requests) == 2


def test_timeout_twice_raises_after_exactly_two_attempts():
    opener = FakeOpener(TimeoutError("slow"))
    with pytest.raises(RunPodError, match="failed after 2 attempts: timed out"):
        provider(opener, timeout=5)("sales", "welding")
    assert len(opener.requests) == 2


@pytest.mark.parametrize("transient", [
    http_error(500), http_error(503), http_error(429),
    urllib.error.URLError("dns"), ConnectionResetError(),
])
def test_transient_failures_get_one_retry(transient):
    opener = FakeOpener(transient, ok_body)
    provider(opener).precompute()
    assert len(opener.requests) == 2


def test_job_still_queued_is_retried():
    opener = FakeOpener({"status": "IN_QUEUE"}, ok_body)
    provider(opener).precompute()
    assert len(opener.requests) == 2


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_client_errors_are_not_retried(code):
    opener = FakeOpener(http_error(code))
    with pytest.raises(RunPodError) as err:
        provider(opener).precompute()
    assert len(opener.requests) == 1
    assert KEY not in str(err.value)


# ---- bad responses (never retried) ----

BAD_BODIES = {
    "not json": b"<html>gateway</html>",
    "json list": b"[1, 2]",
    "failed job": {"status": "FAILED", "error": "CUDA out of memory"},
    "no output": {"status": "COMPLETED"},
    "worker error": {"status": "COMPLETED", "output": {"error": "too many texts: 300 (maximum 256)"}},
    "wrong count": completed([[1.0, 0.0]]),
    "not numbers": completed([["a", "b"]] * 3),
    "ragged": {"status": "COMPLETED", "output": {"embeddings": [[1.0, 0.0], [1.0], [1.0, 0.0]], "model": MODEL}},
    "empty vectors": {"status": "COMPLETED", "output": {"embeddings": [[], [], []], "model": MODEL}},
    "dim mismatch": completed([[1.0, 0.0]] * 3, dim=384),
    "wrong model": {"status": "COMPLETED", "output": {"embeddings": [[1.0, 0.0]] * 3, "model": "other/model"}},
    "embeddings missing": {"status": "COMPLETED", "output": {"model": MODEL}},
}


@pytest.mark.parametrize("name", BAD_BODIES)
def test_bad_responses_raise_a_clear_error_without_retry(name):
    opener = FakeOpener(BAD_BODIES[name])
    with pytest.raises(RunPodError):
        provider(opener).precompute()
    assert len(opener.requests) == 1


def test_error_text_from_the_worker_is_shown_but_the_key_is_redacted():
    body = {"status": "FAILED", "error": f"boom with {KEY} inside"}
    with pytest.raises(RunPodError) as err:
        provider(FakeOpener(body)).precompute()
    assert "boom" in str(err.value) and KEY not in str(err.value)


# ---- the key is never logged or shown ----

def test_key_never_appears_in_logs_errors_or_repr(caplog):
    caplog.set_level(logging.DEBUG)
    p = provider(FakeOpener(TimeoutError("slow")))
    with pytest.raises(RunPodError) as err:
        p("sales", "welding")
    assert "retrying" in caplog.text
    for text in (caplog.text, str(err.value), repr(err.value), repr(p), repr(p._model)):
        assert KEY not in text


# ---- configuration ----

def test_missing_env_vars_raise_config_error(monkeypatch):
    with pytest.raises(RunPodConfigError, match="RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID"):
        RunPodEmbeddingProvider.from_skills(SKILLS)
    monkeypatch.setenv("RUNPOD_API_KEY", KEY)
    with pytest.raises(RunPodConfigError):
        RunPodEmbeddingProvider.from_skills(SKILLS)
    assert not runpod_configured()


def test_env_vars_are_used_and_blank_values_do_not_count(monkeypatch):
    monkeypatch.setenv("RUNPOD_API_KEY", "  ")
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", ENDPOINT)
    assert not runpod_configured()
    monkeypatch.setenv("RUNPOD_API_KEY", KEY)
    assert runpod_configured()
    opener = FakeOpener(ok_body)
    RunPodEmbeddingProvider.from_skills(SKILLS, opener=opener).precompute()
    assert opener.requests[0].get_header("Authorization") == f"Bearer {KEY}"


@pytest.mark.parametrize("endpoint", ["a/b", "../x", "a b", "a?x=1"])
def test_endpoint_id_with_odd_characters_is_rejected(endpoint):
    with pytest.raises(RunPodConfigError):
        RunPodEmbeddingProvider.from_skills(SKILLS, api_key=KEY, endpoint_id=endpoint)


def test_non_https_base_url_is_rejected():
    with pytest.raises(RunPodConfigError):
        RunPodEmbeddingProvider.from_skills(SKILLS, api_key=KEY, endpoint_id=ENDPOINT, base_url="http://x")


# ---- adapter: use RunPod when configured, degrade when not ----

@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("RUNPOD_API_KEY", KEY)
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", ENDPOINT)


def patch_http(monkeypatch, *script):
    opener = FakeOpener(*script)
    monkeypatch.setattr(urllib.request, "urlopen", opener)
    return opener


def run_match(profile, roles, skills, **kw):
    return HussainMatchingProvider(skills_catalogue=skills, **kw).match(profile, roles, None, [])


def role_by_id(matches, role_id):
    return next(m for m in matches if m["role_id"] == role_id)


def test_adapter_uses_runpod_when_configured(monkeypatch, configured, cs_student, roles, skills_catalogue):
    opener = patch_http(monkeypatch, same_vector_for_everything)
    smart = role_by_id(run_match(cs_student, roles, skills_catalogue), "data_analyst")
    monkeypatch.delenv("RUNPOD_API_KEY")
    plain = role_by_id(run_match(cs_student, roles, skills_catalogue), "data_analyst")
    assert smart["score_breakdown"]["skills"] > plain["score_breakdown"]["skills"]
    assert DEGRADED_CAVEAT not in smart["caveats"]
    assert DEGRADED_CAVEAT in plain["caveats"]
    assert len(opener.requests) == 1


def test_adapter_respects_not_equivalent(monkeypatch, configured, cs_student, roles, skills_catalogue):
    patch_http(monkeypatch, same_vector_for_everything)
    free = role_by_id(run_match(cs_student, roles, skills_catalogue), "data_analyst")
    ids = [s["skill_id"] for s in skills_catalogue]
    pairs = [[a, b] for a in ("python", "sql") for b in ids if a != b]
    blocked = role_by_id(
        run_match(cs_student, roles, skills_catalogue, not_equivalent=pairs), "data_analyst")
    assert blocked["score_breakdown"]["skills"] < free["score_breakdown"]["skills"]
    assert DEGRADED_CAVEAT not in blocked["caveats"]


def test_adapter_missing_env_runs_exact_only_with_caveat(monkeypatch, cs_student, roles, skills_catalogue):
    opener = patch_http(monkeypatch, RuntimeError("no HTTP expected"))
    matches = run_match(cs_student, roles, skills_catalogue)
    assert matches and all(DEGRADED_CAVEAT in m["caveats"] for m in matches)
    assert opener.requests == []


@pytest.mark.parametrize("failure", [
    TimeoutError("slow"), http_error(500), http_error(401),
    {"status": "FAILED", "error": "x"}, b"not json",
])
def test_adapter_falls_back_when_the_call_fails(
        monkeypatch, configured, cs_student, roles, skills_catalogue, failure):
    patch_http(monkeypatch, failure)
    matches = run_match(cs_student, roles, skills_catalogue)
    assert matches and all(DEGRADED_CAVEAT in m["caveats"] for m in matches)
    baseline = role_by_id(matches, "data_analyst")["score_breakdown"]["skills"]
    monkeypatch.delenv("RUNPOD_API_KEY")
    exact = role_by_id(run_match(cs_student, roles, skills_catalogue), "data_analyst")
    assert exact["score_breakdown"]["skills"] == baseline


def test_adapter_failure_does_not_log_the_key(
        monkeypatch, configured, caplog, cs_student, roles, skills_catalogue):
    caplog.set_level(logging.DEBUG)
    patch_http(monkeypatch, TimeoutError("slow"))
    run_match(cs_student, roles, skills_catalogue)
    assert "Semantic matching unavailable" in caplog.text and KEY not in caplog.text


def test_adapter_pauses_runpod_after_a_failure_then_retries(
        monkeypatch, configured, cs_student, roles, skills_catalogue):
    opener = patch_http(monkeypatch, TimeoutError("slow"), TimeoutError("slow"), same_vector_for_everything)
    clock = [1000.0]
    monkeypatch.setattr("app.services.hussain_matching.backend_adapter.time.monotonic", lambda: clock[0])
    adapter = HussainMatchingProvider(skills_catalogue=skills_catalogue, retry_after_seconds=60)

    adapter.match(cs_student, roles, None, [])
    assert len(opener.requests) == 2  # first attempt + one retry
    adapter.match(cs_student, roles, None, [])
    assert len(opener.requests) == 2  # paused: no new HTTP calls
    clock[0] += 61
    ok = adapter.match(cs_student, roles, None, [])
    assert len(opener.requests) == 3
    assert all(DEGRADED_CAVEAT not in m["caveats"] for m in ok)
    adapter.match(cs_student, roles, None, [])
    assert len(opener.requests) == 3  # embeddings cached after success


def test_explicit_similarity_overrides_runpod_and_adds_no_caveat(
        monkeypatch, configured, cs_student, roles, skills_catalogue):
    opener = patch_http(monkeypatch, RuntimeError("no HTTP expected"))
    matches = run_match(cs_student, roles, skills_catalogue, similarity=lambda a, b: 0.0)
    assert all(DEGRADED_CAVEAT not in m["caveats"] for m in matches)
    assert opener.requests == []


def test_degraded_caveat_text_and_env_names():
    assert DEGRADED_CAVEAT == "Semantic matching unavailable; exact skill matching only (degraded)"
    assert runpod_client.ENV_API_KEY == "RUNPOD_API_KEY"
    assert runpod_client.ENV_ENDPOINT_ID == "RUNPOD_ENDPOINT_ID"
