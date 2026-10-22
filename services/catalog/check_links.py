"""Check every URL in data/resources.json, data/projects.json and
docs/source-register.md, and write docs/link-check-report.md.

Run from the repo root (needs internet):
    python -m services.catalog.check_links

A site that refuses automated checks (401/403/429, or a bot-challenge page
served with 200) is reported as "BLOCKED (needs manual check)", never "OK".
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ["data/resources.json", "data/projects.json", "docs/source-register.md"]
REPORT = ROOT / "docs" / "link-check-report.md"
URL_RE = re.compile(r"https?://[^\s\"'<>`|)\]]+")
BLOCKED = "BLOCKED (needs manual check)"
BOT_PAGE_MARKERS = ("just a moment", "not a bot", "access denied", "attention required")


def extract_urls(text: str) -> list[str]:
    """URLs in text. Templates such as .../details/<code> are skipped."""
    urls = []
    for m in URL_RE.finditer(text):
        if text[m.end():m.end() + 1] == "<":
            continue
        urls.append(m.group(0).rstrip(".,;:"))
    return urls


def collect_urls(root: Path = ROOT) -> dict[str, list[str]]:
    """url -> files it appears in (sorted by url)."""
    found: dict[str, set[str]] = {}
    for rel in SOURCES:
        for url in extract_urls((root / rel).read_text(encoding="utf-8")):
            found.setdefault(url, set()).add(rel)
    return {u: sorted(found[u]) for u in sorted(found)}


def manually_checked_urls(root: Path = ROOT) -> set[str]:
    """URLs Jawad checked in a browser: resources with checked_by "Jawad..."
    and source-register rows that say "manually by Jawad"."""
    manual: set[str] = set()
    for r in json.loads((root / "data" / "resources.json").read_text(encoding="utf-8"))["resources"]:
        if r.get("checked_by", "").startswith("Jawad"):
            manual.update(extract_urls(r["url"]))
    for line in (root / "docs" / "source-register.md").read_text(encoding="utf-8").splitlines():
        if "manually by jawad" in line.lower():
            manual.update(extract_urls(line))
    return manual


def classify(status: int | None, body: str = "", error: str | None = None) -> str:
    if error is not None:
        return f"ERROR ({error})"
    if status in (401, 403, 429) or any(m in body.lower() for m in BOT_PAGE_MARKERS):
        return BLOCKED
    if status is not None and 200 <= status < 400:
        return "OK"
    if status in (404, 410):
        return f"BROKEN (HTTP {status})"
    return f"HTTP {status}"


def check(url: str, timeout: int = 20) -> tuple[int | None, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 mustaqbal-link-check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(20000).decode("utf-8", "replace")
            title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            return resp.status, classify(resp.status, title.group(1) if title else "")
    except urllib.error.HTTPError as e:
        return e.code, classify(e.code)
    except Exception as e:  # network errors, timeouts, TLS problems
        return None, classify(None, error=type(e).__name__)


def main() -> None:
    urls = collect_urls()
    manual = manually_checked_urls()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = []
    for url, files in urls.items():
        status, result = check(url)
        rows.append((url, status, result, "yes" if url in manual else "no", ", ".join(files)))
        print(f"{result:30s} {status!s:>4}  manual={rows[-1][3]:3s}  {url}")
        time.sleep(1)  # be polite to every host

    counts: dict[str, int] = {}
    for r in rows:
        key = r[2].split(" (")[0]
        counts[key] = counts.get(key, 0) + 1
    lines = [
        "# Link check report",
        "",
        f"Generated {today} (UTC) by `python -m services.catalog.check_links`, which checks every URL in "
        + ", ".join(f"`{s}`" for s in SOURCES) + ".",
        "",
        f"Summary: {len(rows)} URLs. " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + ".",
        "",
        f"`{BLOCKED}` means the site refused an automated request (HTTP 401/403/429 or a bot-challenge page). "
        "It is **not** a pass: someone has to open it in a browser.",
        "",
        "| URL | HTTP status | result | checked manually by Jawad | found in |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| {u} | {s if s is not None else '-'} | {r} | {m} | {f} |" for u, s, r, m, f in rows]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
