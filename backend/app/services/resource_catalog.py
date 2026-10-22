"""Resource catalog — internal-only fixture. No public Resource DTO exists
in the contract (only a bare `resource_id` string appears inside a roadmap
step), so this shape is ours to design, per Milestone 5 section F.

Every resource here is explicitly synthetic/unverified: no real course
URL, price, provider name or certificate is invented (COMPLIANCE.md: "no
invented... resources"). `cost` is always 0.0 and `verified` is always
False until Jawad's real resource dataset replaces this catalog. Coverage
is intentionally partial — several fixture-role skills (e.g. "statistics",
"accounting", "mechanics") have no resource yet, so roadmap generation can
demonstrate the honest "no resource available" path rather than fabricate
one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ResourceFixture:
    resource_id: str
    skill_id: str
    title: str
    estimated_hours: float
    cost: float = 0.0
    verified: bool = False
    # Additive (Milestone 6D-2B): None for every existing fixture resource
    # above, unchanged. CachedResourceCatalog (resource_catalog_cached.py)
    # populates these from Jawad's real data. No frozen public DTO has a
    # matching field — RoadmapStep is {skill_id, resource_id,
    # estimated_hours, reason} only — so url is for future use and
    # provenance is folded into RoadmapStep.reason by RoadmapService,
    # never exposed as its own field.
    url: str | None = None
    provenance: str | None = None


class ResourceCatalogProvider(Protocol):
    def list_resources(self) -> list[ResourceFixture]:
        """Return the currently available placeholder learning resources."""
        ...


_RESOURCES: tuple[ResourceFixture, ...] = (
    ResourceFixture("resource_sql_basics_001", "sql", "Practice: SQL query fundamentals", 4.0),
    ResourceFixture("resource_python_basics_001", "python", "Practice: Python scripting fundamentals", 5.0),
    ResourceFixture(
        "resource_dataviz_basics_001",
        "data_visualization",
        "Practice: building basic charts from tabular data",
        3.0,
    ),
    ResourceFixture("resource_excel_basics_001", "excel", "Practice: spreadsheet formulas and pivot tables", 3.0),
    ResourceFixture(
        "resource_finmodel_basics_001",
        "financial_modeling",
        "Practice: building a simple 3-statement model",
        6.0,
    ),
    ResourceFixture("resource_cad_basics_001", "cad", "Practice: basic parametric CAD modeling", 6.0),
    ResourceFixture(
        "resource_sustainability_reporting_001",
        "sustainability_reporting",
        "Practice: drafting a basic sustainability report outline",
        4.0,
    ),
)


class FixtureResourceCatalog:
    """Deterministic, in-memory stand-in for Jawad's real resource catalog."""

    def list_resources(self) -> list[ResourceFixture]:
        return list(_RESOURCES)
