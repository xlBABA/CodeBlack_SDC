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

_DEFAULT_PROVENANCE_WARNING = (
    "Illustrative demonstration SDG mappings only; not a United Nations "
    "endorsement or official certification, and not yet Jawad's verified "
    "role/skill SDG dataset."
)


@dataclass
class SdgOutcome:
    payload: SdgPayload
    warnings: list[str]


class SdgService:
    def __init__(self, catalog: SdgCatalogProvider, provenance_warning: str | None = None) -> None:
        self._catalog = catalog
        # None preserves the original fixture-mode text exactly (every
        # existing call site that doesn't pass this keeps today's exact
        # behavior). A caller only needs to override it when `catalog`
        # isn't actually FixtureSdgCatalog, since otherwise this text
        # becomes factually wrong ("not yet Jawad's verified... dataset"
        # while serving exactly that dataset) — see
        # app.api.v1.endpoints.sdgs.sdg_provenance_warning().
        self._provenance_warning = provenance_warning or _DEFAULT_PROVENANCE_WARNING

    def get_mappings(self, role_id: str) -> SdgOutcome:
        mapping_set = self._catalog.get(role_id)
        if mapping_set is None:
            return SdgOutcome(
                payload=SdgPayload(role_sdg_mappings=[], skill_sdg_mappings=[]),
                warnings=[
                    f"No SDG mapping exists yet for role_id '{role_id}' in the "
                    f"current catalog. {self._provenance_warning}"
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
        return SdgOutcome(payload=payload, warnings=[self._provenance_warning])
