"""Skill normalization: map raw skill strings to canonical skill_ids.

Deterministic and human-reviewable: every mapping comes from the skills
catalogue (skill_id, name, aliases). Nothing is guessed. Unknown skills are
reported back so the user can correct them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

PROFICIENCY_ORDER = {None: 0, "beginner": 1, "intermediate": 2, "advanced": 3}


def _key(text: str) -> str:
    """Comparison key: lowercase, drop spaces and punctuation, keep + and #.

    "React.js" -> "reactjs", "C++" -> "c++", "Structured Query Language" ->
    "structuredquerylanguage".
    """
    return re.sub(r"[^a-z0-9+#]", "", text.lower())


@dataclass(frozen=True)
class NormalizedSkill:
    raw: str
    skill_id: str | None
    name: str | None
    confidence: float  # 1.0 for catalogue hit, 0.0 for unknown
    method: str  # "id" | "name" | "alias" | "unknown"


class SkillNormalizer:
    def __init__(self, skills: list[dict]):
        self._by_id: dict[str, dict] = {}
        self._lookup: dict[str, tuple[str, str]] = {}
        self._phrases: list[tuple[re.Pattern, str]] = []

        for s in skills:
            sid = s["skill_id"]
            if sid in self._by_id:
                raise ValueError(f"Duplicate skill_id in catalogue: {sid}")
            self._by_id[sid] = s

        for s in skills:
            sid = s["skill_id"]
            self._register(sid, sid, "id")
            self._register(s["name"], sid, "name")
            for alias in s.get("aliases", []):
                self._register(alias, sid, "alias")
            for phrase in [s["name"], *s.get("aliases", [])]:
                pattern = re.compile(
                    r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"
                )
                self._phrases.append((pattern, sid))

    def _register(self, text: str, sid: str, method: str) -> None:
        key = _key(text)
        if not key:
            return
        existing = self._lookup.get(key)
        if existing and existing[0] != sid:
            raise ValueError(
                f"Ambiguous alias '{text}' maps to both {existing[0]} and {sid}"
            )
        if not existing:
            self._lookup[key] = (sid, method)

    def name_of(self, skill_id: str) -> str:
        return self._by_id[skill_id]["name"]

    def has(self, skill_id: str) -> bool:
        return skill_id in self._by_id

    def normalize(self, raw: str) -> NormalizedSkill:
        hit = self._lookup.get(_key(raw))
        if not hit:
            return NormalizedSkill(raw, None, None, 0.0, "unknown")
        sid, method = hit
        return NormalizedSkill(raw, sid, self.name_of(sid), 1.0, method)

    def normalize_profile_skills(
        self, skill_refs: list[dict]
    ) -> tuple[dict[str, str | None], list[str]]:
        """Return ({skill_id: proficiency}, warnings).

        Accepts contract SkillRef dicts. A valid skill_id wins; otherwise the
        name is normalized. Duplicates keep the highest proficiency.
        """
        resolved: dict[str, str | None] = {}
        warnings: list[str] = []
        for ref in skill_refs:
            sid = ref.get("skill_id")
            if not (sid and self.has(sid)):
                result = self.normalize(ref.get("name") or sid or "")
                sid = result.skill_id
            if sid is None:
                label = ref.get("name") or ref.get("skill_id") or "<empty>"
                warnings.append(
                    f"Skill '{label}' is not in the supported catalogue and was "
                    "not used for matching. Please check the spelling or pick a "
                    "listed skill."
                )
                continue
            prof = ref.get("proficiency")
            if prof not in PROFICIENCY_ORDER:
                warnings.append(
                    f"Unknown proficiency '{prof}' for {sid}; treated as unspecified."
                )
                prof = None
            if sid not in resolved or PROFICIENCY_ORDER[prof] > PROFICIENCY_ORDER[resolved[sid]]:
                resolved[sid] = prof
        return resolved, warnings

    def find_in_text(self, text: str) -> set[str]:
        """Skill_ids whose name or alias appears as a whole phrase in text."""
        lowered = (text or "").lower()
        return {sid for pattern, sid in self._phrases if pattern.search(lowered)}
