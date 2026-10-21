from services.trends.aggregate import DIRECTION_THRESHOLD, build_trend_signal, compute_direction
from services.trends.github_client import WindowCount


def _window(count: int, incomplete: bool = False, topic="sql", start="2026-09-21", end="2026-10-21"):
    return WindowCount(topic=topic, start=start, end=end, total_count=count,
                       incomplete=incomplete, retrieved_at="2026-10-21T12:00:00Z")


def test_rising_needs_more_than_15_percent():
    assert compute_direction(100, 116) == "rising"   # +16%
    assert compute_direction(100, 115) == "stable"    # exactly +15%, not "more than"


def test_falling_needs_more_than_15_percent():
    assert compute_direction(100, 84) == "falling"    # -16%
    assert compute_direction(100, 85) == "stable"     # exactly -15%


def test_small_change_is_stable():
    assert compute_direction(100, 105) == "stable"


def test_zero_baseline_with_zero_current_is_stable_not_a_division_error():
    assert compute_direction(0, 0) == "stable"


def test_zero_baseline_with_nonzero_current_is_unknown_not_infinite_percent():
    assert compute_direction(0, 5) == "unknown"


def test_missing_window_is_unknown():
    assert compute_direction(None, 10) == "unknown"
    assert compute_direction(10, None) == "unknown"


def test_threshold_constant_is_15_percent():
    assert DIRECTION_THRESHOLD == 0.15


def test_build_trend_signal_shape_matches_contract():
    current = _window(130)
    previous = _window(100)
    signal = build_trend_signal("sql", current, previous, ["data_analyst"], retrieved_at="2026-10-21T12:00:00Z")
    expected_keys = {
        "signal_id", "skill_id", "source_id", "signal_type", "metric_name",
        "metric_value", "unit", "observed_at", "retrieved_at", "direction",
        "confidence_note", "role_ids",
    }
    # every contract field, plus exactly one documented extension
    assert set(signal.keys()) == expected_keys | {"change_since_last_snapshot"}
    assert signal["skill_id"] == "sql"
    assert signal["direction"] == "rising"  # +30%
    assert signal["metric_value"] == 130
    assert signal["role_ids"] == ["data_analyst"]
    assert "not verified hiring demand" in signal["confidence_note"].lower() or \
           "not a hiring" in signal["confidence_note"].lower() or \
           "hiring demand" in signal["confidence_note"].lower()


def test_incomplete_results_force_unknown_direction():
    current = _window(130, incomplete=True)
    previous = _window(100)
    signal = build_trend_signal("sql", current, previous, [], retrieved_at="2026-10-21T12:00:00Z")
    assert signal["direction"] == "unknown"
    assert "incomplete" in signal["confidence_note"].lower()


def test_missing_current_window_is_unknown_and_has_no_metric_value():
    signal = build_trend_signal("sql", None, _window(100), [], retrieved_at="2026-10-21T12:00:00Z")
    assert signal["direction"] == "unknown"
    assert signal["metric_value"] is None
