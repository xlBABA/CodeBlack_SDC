"""Cached SDG mapping dataset — Jawad's verified sdg_mappings.json
(app/data/cached/sdg_mappings.json; byte-identical copy of
feat/jawad-trends-data:data/sdg_mappings.json as of commit 2838340).

Milestone 6D-2A added import and validation (load_cached_sdg_mappings()).
Milestone 6D-2C adds CachedSdgCatalog, satisfying
app.services.sdg_catalog.SdgCatalogProvider — still not wired into GET
/sdgs/{role_id} or FixtureSdgCatalog (which, unlike
get_role_catalog()/get_matching_provider(), currently has no CATALOG_MODE
awareness at all).
"""
from __future__ import annotations

from app.services.role_catalog_cached import CachedCatalogError, _load_json, _require_dict, load_cached_roles
from app.services.sdg_catalog import RoleSdgFixture, RoleSdgMappingSet, SkillSdgFixture

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


def _required_skill_ids_for_role(role_id: str) -> set[str]:
    role = next((r for r in load_cached_roles() if r.role_id == role_id), None)
    if role is None:
        return set()
    return {req.skill_id for req in role.required_skills}


class CachedSdgCatalog:
    """Satisfies app.services.sdg_catalog.SdgCatalogProvider using
    Jawad's real, cached SDG mapping dataset exclusively — never mixes
    in anything from FixtureSdgCatalog. A role_id outside Jawad's own
    canonical set (e.g. our fixture-only mechanical_design_engineer,
    sustainability_coordinator) has no entry in role_sdg_mappings at
    all, so get() returns None for it — honest empty, never an
    accidental join to a fixture-only role_id. RoleSdgMappingSet.role_sdg
    is a tuple, so a role with multiple SDGs (e.g. accountant, 2;
    civil_engineer, 2) is preserved exactly, with no schema change
    needed. Not wired into GET /sdgs/{role_id} or any FastAPI dependency
    yet (Milestone 6D-2C scope: adapter implementation and testing only).
    """

    def get(self, role_id: str) -> RoleSdgMappingSet | None:
        mappings = load_cached_sdg_mappings()
        role_sdg = tuple(
            RoleSdgFixture(sdg_id=m["sdg_id"], reason=m["reason"])
            for m in mappings["role_sdg_mappings"]
            if m["role_id"] == role_id
        )
        if not role_sdg:
            return None

        relevant_skill_ids = _required_skill_ids_for_role(role_id)
        skill_sdg = tuple(
            SkillSdgFixture(skill_id=m["skill_id"], sdg_id=m["sdg_id"], reason=m["reason"])
            for m in mappings["skill_sdg_mappings"]
            if m["skill_id"] in relevant_skill_ids
        )
        return RoleSdgMappingSet(role_id=role_id, role_sdg=role_sdg, skill_sdg=skill_sdg)
