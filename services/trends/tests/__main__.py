"""Offline test runner (no pytest dependency). Run from the repo root:

    python -m services.trends.tests

Every test module here is fully offline: fake transport, fake clock, no
real sleeps, no network.
"""
import sys
import traceback
from importlib import import_module

MODULES = [
    "test_queries",
    "test_github_client",
    "test_aggregate",
    "test_snapshot",
    "test_ingest",
]


def main() -> int:
    passed = 0
    failed = 0
    for mod_name in MODULES:
        mod = import_module(f"services.trends.tests.{mod_name}")
        for name in sorted(dir(mod)):
            if not name.startswith("test_"):
                continue
            fn = getattr(mod, name)
            if not callable(fn):
                continue
            try:
                fn()
                passed += 1
            except Exception:
                failed += 1
                print(f"FAILED: {mod_name}.{name}")
                traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
