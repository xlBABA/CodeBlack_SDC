"""Milestone 12B-4/12B-5: strict loader/validator for a FUTURE,
not-yet-delivered backend/app/data/cached/skill_not_equivalent.json file —
Jawad's upcoming "these two skills are related but not equivalent"
exclusion list for Hussain's semantic matcher
(app.services.hussain_matching.backend_adapter.HussainMatchingProvider's
`not_equivalent` constructor parameter).

SCOPE / RESTRICTIONS:
- The file does not exist in this repo yet. This module ONLY validates and
  loads it IF present; it is NOT imported or wired into careers.py or
  HussainMatchingProvider — see careers.py's own docstring / the 12B-4/
  12B-5 reports for the exact minimal wiring change to make once Jawad's
  actual reviewed PR lands. Importing this module today has zero effect
  on production matching behavior.
- No exclusion pair is invented anywhere here. Every pair this module ever
  returns is read verbatim from the on-disk file.

SCHEMA (Milestone 12B-5: Jawad's explicitly proposed format — the file
itself still doesn't exist, but its shape is now documented rather than
assumed):

    {
      "not_equivalent": [
        ["python", "javascript"],
        ["excel", "vba"]
      ]
    }

A top-level JSON OBJECT with exactly one key, "not_equivalent", whose
value is a JSON array of 2-element pairs of DIFFERENT skill_id strings.
Rejected: a bare top-level array (the pre-12B-5 assumption, now
superseded), a missing "not_equivalent" key, any unknown top-level key,
and a "not_equivalent" value that isn't itself a JSON array. The returned
value — the validated inner array only — is exactly the
`list[list[str]]` shape the ONLY current consumer actually accepts
(app.services.hussain_matching.embeddings.EmbeddingProvider.__init__ and
app.services.hussain_matching.backend_adapter.HussainMatchingProvider.
_applicable_pairs(), both of which take/expect `list[list[str]]`, each
inner list exactly two DIFFERENT skill_id strings) — so this loader's
output can be passed straight into HussainMatchingProvider(not_equivalent=
...) with no further transformation, once that wiring is made.

If Jawad's actual delivered file still differs from this proposed
envelope (e.g. an additional required field, a different key name), this
loader and its tests must be revised again before use — this documented
proposal is not a substitute for his real, reviewed file.

VALIDATION PHILOSOPHY (deliberately asymmetric, matching this codebase's
existing cached-data conventions — see role_catalog_cached.py/
trend_provider_cached.py):
- Missing file -> `[]` (requirement 4: this is an OPTIONAL enrichment;
  matching must work exactly as today when it hasn't arrived yet).
- File present but structurally invalid in ANY way (not an object, a
  missing/unknown top-level key, a "not_equivalent" value that isn't a
  list, a pair that isn't exactly two different non-empty strings, an
  unknown skill_id not in the real app/data/cached/skills.json, or a
  duplicate pair) -> raises CachedCatalogError. Never silently drops a
  bad entry and never substitutes an invented value in its place
  (requirement 4: "fail safely without silently substituting invented
  values").
- Malformed JSON syntax -> json.JSONDecodeError propagates unwrapped,
  exactly like role_catalog_cached.py/trend_provider_cached.py's own
  _load_json() calls do for their required files - never swallowed.

Unknown-skill_id handling here is intentionally STRICTER than
HussainMatchingProvider._applicable_pairs()'s own runtime behavior (which
silently skips an inapplicable pair with a logged warning, because that
function sees only whatever subset of skills the *current* match request's
catalogue happens to contain). This module instead validates the FILE's
own integrity against the full canonical skill catalog
(app/data/cached/skills.json) ahead of time - catching a typo'd skill_id
at review time, not silently at request time.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.services.role_catalog_cached import CachedCatalogError, _load_json

_SKILL_NOT_EQUIVALENT_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "cached" / "skill_not_equivalent.json"
)

# The only top-level key Jawad's proposed envelope defines (Milestone
# 12B-5). Any other key is unsupported — never silently ignored, so a
# typo'd or extra field is caught at review time rather than quietly
# doing nothing.
_REQUIRED_TOP_LEVEL_KEYS = {"not_equivalent"}
_ALLOWED_TOP_LEVEL_KEYS = _REQUIRED_TOP_LEVEL_KEYS


def _canonical_skill_ids() -> set[str]:
    skills_doc = _load_json("skills.json")
    return {s["skill_id"] for s in skills_doc["skills"]}


def _validate_pair(pair: object, index: int, skill_ids: set[str]) -> list[str]:
    context = f"skill_not_equivalent.json.not_equivalent[{index}]"
    if not isinstance(pair, list):
        raise CachedCatalogError(
            f"{context}: expected a list of two skill_ids, got {type(pair).__name__}"
        )
    if len(pair) != 2:
        raise CachedCatalogError(f"{context}: expected exactly 2 skill_ids, got {len(pair)}")
    for item in pair:
        if not isinstance(item, str) or not item:
            raise CachedCatalogError(
                f"{context}: each skill_id must be a non-empty string, got {item!r}"
            )
    if pair[0] == pair[1]:
        raise CachedCatalogError(
            f"{context}: a pair must name two DIFFERENT skill_ids, got {pair!r} twice"
        )
    unknown = [sid for sid in pair if sid not in skill_ids]
    if unknown:
        raise CachedCatalogError(
            f"{context}: unknown skill_id(s) {unknown} not present in cached skills.json"
        )
    return list(pair)


def load_skill_not_equivalent_pairs() -> list[list[str]]:
    """Load and strictly validate skill_not_equivalent.json, or return `[]`
    if the file does not exist yet (requirement 4 — this is an optional,
    not-yet-delivered file; its absence must never block matching).

    Expects Jawad's proposed envelope: a top-level JSON object with
    exactly one key, "not_equivalent", holding the array of pairs (see
    module docstring). Returns just that validated inner array — already
    in the exact `list[list[str]]` shape HussainMatchingProvider's
    `not_equivalent` parameter expects.

    Raises CachedCatalogError on any structural problem in the file (not
    an object, a missing/unknown top-level key, a "not_equivalent" value
    that isn't a list, a malformed pair, an unknown skill_id, a duplicate
    pair) — never silently drops or "fixes" bad data. Raises
    json.JSONDecodeError (unwrapped) if the file's contents are not valid
    JSON at all, matching this codebase's existing cached-loader
    convention for a present-but-unreadable file.
    """
    if not _SKILL_NOT_EQUIVALENT_PATH.is_file():
        return []

    raw = json.loads(_SKILL_NOT_EQUIVALENT_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CachedCatalogError(
            "skill_not_equivalent.json: expected a top-level JSON object with a "
            f"'not_equivalent' key, got {type(raw).__name__}"
        )

    missing = _REQUIRED_TOP_LEVEL_KEYS - raw.keys()
    if missing:
        raise CachedCatalogError(f"skill_not_equivalent.json: missing required key(s) {sorted(missing)}")
    unsupported = raw.keys() - _ALLOWED_TOP_LEVEL_KEYS
    if unsupported:
        raise CachedCatalogError(
            f"skill_not_equivalent.json: unsupported top-level key(s) {sorted(unsupported)}"
        )

    raw_pairs = raw["not_equivalent"]
    if not isinstance(raw_pairs, list):
        raise CachedCatalogError(
            "skill_not_equivalent.json: 'not_equivalent' must be a JSON array, "
            f"got {type(raw_pairs).__name__}"
        )

    skill_ids = _canonical_skill_ids()
    pairs: list[list[str]] = []
    seen: set[frozenset[str]] = set()
    for index, raw_pair in enumerate(raw_pairs):
        pair = _validate_pair(raw_pair, index, skill_ids)
        key = frozenset(pair)
        if key in seen:
            raise CachedCatalogError(
                f"skill_not_equivalent.json.not_equivalent[{index}]: duplicate pair {pair!r} "
                "(already listed earlier in the file, in either order)"
            )
        seen.add(key)
        pairs.append(pair)

    return pairs


__all__ = ["load_skill_not_equivalent_pairs", "CachedCatalogError"]
