"""Orchestrates GET /sdgs/{role_id}. Thin passthrough over the fixture
catalog. An unknown role_id is an honest empty envelope (consistent with
/trends' and /projects/recommend's unknown-filter handling), not a 404 —
section E asks for "existing error/envelope conventions," and this route
has nothing resembling a required single resource the way
/projects/simulate does.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.sdgs import RoleSdgMapping, SdgPayload, SkillSdgMapping
from app.services.sdg_catalog import SdgCatalogProvider


@dataclass
class SdgOutcome:
    payload: SdgPayload
    warnings: list[str]


class SdgService:
    def __init__(self, catalog: SdgCatalogProvider) -> None:
        self._catalog = catalog

    def get_mappings(self, role_id: str) -> SdgOutcome:
        mapping_set = self._catalog.get(role_id)
        if mapping_set is None:
            return SdgOutcome(
                payload=SdgPayload(role_sdg_mappings=[], skill_sdg_mappings=[]),
                warnings=[
                    f"No SDG mapping exists yet for role_id '{role_id}' in the "
                    "current placeholder catalog; pending Jawad's verified "
                    "SDG dataset."
                ],
            )

        payload = SdgPayload(
            role_sdg_mappings=[
                RoleSdgMapping(sdg_id=m.sdg_id, reason=m.reason) for m in mapping_set.role_sdg
            ],
            skill_sdg_mappings=[
                SkillSdgMapping(skill_id=m.skill_id, sdg_id=m.sdg_id, reason=m.reason)
                for m in mapping_set.skill_sdg
            ],
        )
        warnings = [
            "Illustrative demonstration SDG mappings only; not a United "
            "Nations endorsement or official certification, and not yet "
            "Jawad's verified role/skill SDG dataset."
        ]
        return SdgOutcome(payload=payload, warnings=warnings)
