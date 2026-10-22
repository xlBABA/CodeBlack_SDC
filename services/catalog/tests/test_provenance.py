"""Provenance coverage: every role, skill, resource, project and trend signal
points at a source_id registered in docs/source-register.md, and every trend
signal has observed_at and retrieved_at. Offline (reads saved snapshots only).

Run from the repo root: python -m services.catalog.tests.test_provenance
"""
import json
import re
import sys
from pathlib import Path

from services.trends import get_trends

ROOT = Path(__file__).resolve().parents[3]
REGISTERED = set(re.findall(r"^\| ([a-z0-9_]+) \|", (ROOT / "docs" / "source-register.md").read_text(encoding="utf-8"), flags=re.M))
ISO_Z = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _load(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def _unregistered(ids):
    return sorted(set(ids) - REGISTERED)


def test_every_role_has_registered_evidence():
    for r in _load("roles.json"):
        assert r["evidence_ids"], r["role_id"]
        assert not _unregistered(r["evidence_ids"] + [r["source_id"]]), r["role_id"]


def test_every_skill_has_registered_sources():
    for s in _load("skills.json")["skills"]:
        assert s["source_ids"], s["skill_id"]
        assert not _unregistered(s["source_ids"]), (s["skill_id"], _unregistered(s["source_ids"]))


def test_every_resource_has_a_registered_source_id():
    for r in _load("resources.json")["resources"]:
        assert r.get("source_id"), r["resource_id"]
        assert not _unregistered([r["source_id"]]), r["resource_id"]


def test_every_project_has_registered_sources():
    for p in _load("projects.json")["projects"]:
        assert p["source_ids"], p["project_id"]
        assert not _unregistered(p["source_ids"]), (p["project_id"], _unregistered(p["source_ids"]))


def test_every_trend_signal_is_registered_and_dated():
    result = get_trends(limit=100)
    assert result["signals"], "no saved trend snapshots to check"
    for sig in result["signals"]:
        assert not _unregistered([sig["source_id"]]), sig["signal_id"]
        assert sig["observed_at"] and ISO_Z.fullmatch(sig["observed_at"]), sig["signal_id"]
        assert sig["retrieved_at"] and ISO_Z.fullmatch(sig["retrieved_at"]), sig["signal_id"]


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
