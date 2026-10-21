from services.trends.github_client import GitHubFetchError, GitHubTrendClient
from services.trends.tests.fakes import FakeClock, ScriptedTransport, github_response, http_error, no_sleep


def test_fetch_window_count_parses_response():
    transport = ScriptedTransport([github_response(42)])
    client = GitHubTrendClient(
        token=None, transport=transport, sleep_fn=no_sleep, clock=FakeClock(["2026-10-21T12:00:00Z"])
    )
    result = client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
    assert result.total_count == 42
    assert result.topic == "sql"
    assert result.incomplete is False
    assert result.retrieved_at == "2026-10-21T12:00:00Z"


def test_fetch_window_count_flags_incomplete_results():
    transport = ScriptedTransport([github_response(42, incomplete=True)])
    client = GitHubTrendClient(transport=transport, sleep_fn=no_sleep, clock=FakeClock(["2026-10-21T12:00:00Z"]))
    result = client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
    assert result.incomplete is True


def test_http_failure_raises_fetch_error_not_a_fake_count():
    transport = ScriptedTransport([http_error("HTTP 403: rate limited")])
    client = GitHubTrendClient(transport=transport, sleep_fn=no_sleep, clock=FakeClock(["2026-10-21T12:00:00Z"]))
    try:
        client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
        raise AssertionError("expected GitHubFetchError")
    except GitHubFetchError:
        pass


def test_unexpected_response_shape_raises():
    transport = ScriptedTransport([{"message": "Bad credentials"}])
    client = GitHubTrendClient(transport=transport, sleep_fn=no_sleep, clock=FakeClock(["2026-10-21T12:00:00Z"]))
    try:
        client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
        raise AssertionError("expected GitHubFetchError")
    except GitHubFetchError:
        pass


def test_query_uses_topic_and_created_range():
    transport = ScriptedTransport([github_response(1)])
    client = GitHubTrendClient(transport=transport, sleep_fn=no_sleep, clock=FakeClock(["2026-10-21T12:00:00Z"]))
    client.fetch_window_count("data-visualization", "2026-09-21", "2026-10-21")
    url, headers = transport.calls[0]
    assert "topic%3Adata-visualization" in url
    assert "created%3A2026-09-21..2026-10-21" in url
    assert "Authorization" not in headers  # no token supplied


def test_token_adds_authorization_header():
    transport = ScriptedTransport([github_response(1)])
    client = GitHubTrendClient(
        token="fake-token-value", transport=transport, sleep_fn=no_sleep, clock=FakeClock(["2026-10-21T12:00:00Z"])
    )
    client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
    _, headers = transport.calls[0]
    assert headers["Authorization"] == "Bearer fake-token-value"


def test_throttle_sleeps_between_calls_without_a_token():
    transport = ScriptedTransport([github_response(1), github_response(2)])
    sleeps: list[float] = []
    client = GitHubTrendClient(
        transport=transport, sleep_fn=sleeps.append, clock=FakeClock(["2026-10-21T12:00:00Z"])
    )
    client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
    client.fetch_window_count("sql", "2026-09-21", "2026-10-21")
    assert len(sleeps) == 1  # throttled before the second call, not the first
    assert sleeps[0] > 0
