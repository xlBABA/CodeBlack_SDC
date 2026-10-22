"""Cached SDG mapping dataset — Jawad's verified sdg_mappings.json
(app/data/cached/sdg_mappings.json; byte-identical copy of
feat/jawad-trends-data:data/sdg_mappings.json as of commit 2838340).

Milestone 6D-2A scope: import and validation ONLY — see
resource_catalog_cached.py's module docstring for the same disclaimer.
Not wired into SdgCatalogProvider, GET /sdgs/{role_id}, or
FixtureSdgCatalog (which, unlike get_role_catalog()/get_matching_provider(),
currently has no CATALOG_MODE awareness at all).
"""
from __future__ import annotations

from app.services.role_catalog_cached import CachedCatalogError, _load_json, _require_dict, load_cached_roles

_REQUIRED_ROLE_MAPPING_FIELDS = {"role_id", "sdg_id", "reason"}
_REQUIRED_SKILL_MAPPING_FIELDS = {"skill_id", "sdg_id", "reason"}


def _canonical_skill_ids() -> set[str]:
    skills_doc = _load_json("skills.json")
    return {s["skill_id"] for s in skills_doc["skills"]}


def _canonical_role_ids() -> set[str]:
    return {role.role_id for role in load_cached_roles()}


def _validate_sdg_id(sdg_id: object, context: str) -> None:
    if not isinstance(sdg_id, int) or isinstance(sdg_id, bool) or not (1 <= sdg_id <= 17):
        raise CachedCatalogError(f"{context}: sdg_id must be an int 1-17, got {sdg_id!r}")


def _validate_reason(reason: object, context: str) -> None:
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        raise CachedCatalogError(f"{context}: reason must be a real, non-trivial string, got {reason!r}")


def _validate_sdg_mappings(
    role_mappings: list[dict], skill_mappings: list[dict], role_ids: set[str], skill_ids: set[str]
) -> None:
    for index, mapping in enumerate(role_mappings):
        context = f"role_sdg_mappings[{index}]"
        missing = _REQUIRED_ROLE_MAPPING_FIELDS - mapping.keys()
        if missing:
            raise CachedCatalogError(f"{context}: missing fields {missing}")
        unsupported = mapping.keys() - _REQUIRED_ROLE_MAPPING_FIELDS
        if unsupported:
            raise CachedCatalogError(f"{context}: unsupported fields {unsupported}")
        if mapping["role_id"] not in role_ids:
            raise CachedCatalogError(f"{context}: unknown role_id '{mapping['role_id']}'")
        _validate_sdg_id(mapping["sdg_id"], f"{context} ({mapping['role_id']})")
        _validate_reason(mapping["reason"], f"{context} ({mapping['role_id']})")

    for index, mapping in enumerate(skill_mappings):
        context = f"skill_sdg_mappings[{index}]"
        missing = _REQUIRED_SKILL_MAPPING_FIELDS - mapping.keys()
        if missing:
            raise CachedCatalogError(f"{context}: missing fields {missing}")
        unsupported = mapping.keys() - _REQUIRED_SKILL_MAPPING_FIELDS
        if unsupported:
            raise CachedCatalogError(f"{context}: unsupported fields {unsupported}")
        if mapping["skill_id"] not in skill_ids:
            raise CachedCatalogError(f"{context}: unknown skill_id '{mapping['skill_id']}'")
        _validate_sdg_id(mapping["sdg_id"], f"{context} ({mapping['skill_id']})")
        _validate_reason(mapping["reason"], f"{context} ({mapping['skill_id']})")

    missing_role_coverage = role_ids - {m["role_id"] for m in role_mappings}
    if missing_role_coverage:
        raise CachedCatalogError(f"Roles missing an SDG mapping: {sorted(missing_role_coverage)}")
    missing_skill_coverage = skill_ids - {m["skill_id"] for m in skill_mappings}
    if missing_skill_coverage:
        raise CachedCatalogError(f"Skills missing an SDG mapping: {sorted(missing_skill_coverage)}")


def load_cached_sdg_mappings() -> dict:
    """Load, validate and return app/data/cached/sdg_mappings.json's
    role_sdg_mappings/skill_sdg_mappings as plain dicts. Raises
    CachedCatalogError on any integrity problem — including incomplete
    coverage of the canonical role/skill set — rather than silently
    inventing a mapping or leaving a gap unreported."""
    doc = _load_json("sdg_mappings.json")
    role_ids = _canonical_role_ids()
    skill_ids = _canonical_skill_ids()

    role_mappings = [
        _require_dict(r, f"role_sdg_mappings[{i}]") for i, r in enumerate(doc.get("role_sdg_mappings") or [])
    ]
    skill_mappings = [
        _require_dict(s, f"skill_sdg_mappings[{i}]") for i, s in enumerate(doc.get("skill_sdg_mappings") or [])
    ]

    _validate_sdg_mappings(role_mappings, skill_mappings, role_ids, skill_ids)
    return {"role_sdg_mappings": role_mappings, "skill_sdg_mappings": skill_mappings}
