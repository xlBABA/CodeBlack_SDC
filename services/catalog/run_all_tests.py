"""Run all of Jawad's test suites in order and print one pass/fail summary.
Offline (no network needed). Run from the repo root:

    python -m services.catalog.run_all_tests
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUITES = [
    ("catalog schema", ["services/catalog/tests/test_roles_schema.py"]),
    ("catalog", ["-m", "services.catalog.tests.test_catalog"]),
    ("provenance", ["-m", "services.catalog.tests.test_provenance"]),
    ("link checker (offline)", ["-m", "services.catalog.tests.test_check_links"]),
    ("sdg", ["-m", "services.sdg.tests.test_sdg"]),
    ("roadmap", ["-m", "services.roadmaps.tests.test_roadmap"]),
    ("projects", ["-m", "services.roadmaps.tests.test_projects"]),
    ("trends", ["-m", "services.trends.tests"]),
]


def main() -> int:
    failed_suites = []
    for name, args in SUITES:
        proc = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
        out = (proc.stdout + proc.stderr).strip()
        counts = re.search(r"(\d+) passed, (\d+) failed", out)
        detail = f"{counts.group(1)} passed, {counts.group(2)} failed" if counts else out.splitlines()[-1] if out else ""
        ok = proc.returncode == 0
        print(f"{'PASS' if ok else 'FAIL'}  {name:24s} {detail}")
        if not ok:
            failed_suites.append(name)
            print("      " + out.replace("\n", "\n      "))
    print()
    if failed_suites:
        print(f"RESULT: FAIL ({len(failed_suites)} of {len(SUITES)} suites failed: {', '.join(failed_suites)})")
        return 1
    print(f"RESULT: PASS (all {len(SUITES)} suites passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
