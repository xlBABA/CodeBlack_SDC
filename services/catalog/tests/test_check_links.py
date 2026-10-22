"""Offline tests for check_links (no network). Run from the repo root:
python -m services.catalog.tests.test_check_links"""
import sys

from services.catalog.check_links import BLOCKED, classify, collect_urls, extract_urls, manually_checked_urls


def test_blocked_sites_are_never_ok():
    for status in (401, 403, 429):
        assert classify(status) == BLOCKED
    assert classify(200, "Just a moment...") == BLOCKED  # Cloudflare challenge served with 200
    assert classify(200, "Making sure you're not a bot!") == BLOCKED


def test_other_results():
    assert classify(200, "Online Retail II") == "OK"
    assert classify(404) == "BROKEN (HTTP 404)"
    assert classify(500) == "HTTP 500"
    assert classify(None, error="URLError") == "ERROR (URLError)"


def test_extract_urls_trims_punctuation_and_skips_templates():
    text = "See https://a.org/x. and (https://b.org/y) and https://c.org/link/details/<code> | https://d.org/z |"
    assert extract_urls(text) == ["https://a.org/x", "https://b.org/y", "https://d.org/z"]


def test_collects_every_resource_and_project_source_url():
    urls = collect_urls()
    assert "https://alison.com/course/thinking-critically" in urls
    assert "https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients" in urls
    assert all(u.startswith("http") for u in urls)


def test_jawads_manual_checks_are_detected():
    manual = manually_checked_urls()
    assert {
        "https://alison.com/course/thinking-critically",
        "https://youtu.be/Vl0H-qTclOg",
        "https://learn.onshape.com/learning-paths/introduction-to-cad",
        "https://youtu.be/xxpc-HPKN28",
    } <= manual
    assert "https://learn.sas.com/course/view.php?id=118" not in manual


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
