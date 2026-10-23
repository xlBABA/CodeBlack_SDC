"""Skill normalization: map raw skill strings to canonical skill_ids.

Deterministic and human-reviewable: every mapping comes from the skills
catalogue (skill_id, name, aliases). Nothing is guessed. Unknown skills are
reported back so the user can correct them.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, Sequence

logger = logging.getLogger(__name__)

PROFICIENCY_ORDER = {None: 0, "beginner": 1, "intermediate": 2, "advanced": 3}


_WORDS = re.compile(r"[a-z0-9+#]+")


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


@dataclass(frozen=True)
class Interpretation:
    """A skill name that is not in the catalogue, mapped to a catalogue skill."""
    raw: str
    skill_id: str
    name: str
    similarity: float
    warning_index: int = -1  # internal: position of the replaced warning
    contains: str | None = None  # set when the raw text contains a known skill phrase

    def message(self) -> str:
        if self.contains is not None:
            return (f'Interpreted "{self.raw}" as {self.name} (it contains "{self.contains}"), '
                    "partial credit; please confirm.")
        return (f'Interpreted "{self.raw}" as {self.name} (similarity {self.similarity:.2f}), '
                "partial credit; please confirm.")


# names -> one (skill_id, similarity) or None per name
Interpreter = Callable[[Sequence[str]], Sequence["tuple[str, float] | None"]]


class SkillNormalizer:
    def __init__(self, skills: list[dict]):
        self._by_id: dict[str, dict] = {}
        self._lookup: dict[str, tuple[str, str]] = {}
        self._phrases: list[tuple[re.Pattern, str]] = []
        self._phrase_texts: list[tuple[str, str]] = []  # (phrase, skill_id), parallel to _phrases

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
                self._phrase_texts.append((phrase, sid))

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
        resolved, warnings, _ = self.interpret_profile_skills(skill_refs)
        return resolved, warnings

    def interpret_profile_skills(
        self, skill_refs: list[dict], interpreter: Interpreter | None = None
    ) -> tuple[dict[str, str | None], list[str], dict[str, Interpretation]]:
        """Like normalize_profile_skills, but unknown names get extra treatment.

        For a name that is not a catalogue name or alias, in this order:
        1. it contains exactly one known skill phrase ("Python (pandas)"): mapped to that
           skill, listed as an interpretation (partial credit, "please confirm");
        2. it is only part of a longer skill name ("Accounting" in "Accounting Software"):
           NOT mapped, the warning gets "Did you mean ...?";
        3. otherwise `interpreter(names)` (embeddings) may map it. It returns one
           (skill_id, similarity) or None per name.

        Interpretations are returned as {skill_id: Interpretation} so the caller can give
        partial credit and explain them. Catalogue hits always win. If nothing maps, or
        the interpreter raises, an unknown skill is dropped with the usual warning.
        """
        resolved: dict[str, str | None] = {}
        warnings: list[str | None] = []
        unknown: list[tuple[int, str, str | None]] = []  # (warning index, name, proficiency)
        for ref in skill_refs:
            sid = ref.get("skill_id")
            if not (sid and self.has(sid)):
                result = self.normalize(ref.get("name") or sid or "")
                sid = result.skill_id
            if sid is None:
                label = ref.get("name") or ref.get("skill_id") or "<empty>"
                if ref.get("name"):
                    unknown.append((len(warnings), ref["name"], ref.get("proficiency")))
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

        interpreted: dict[str, Interpretation] = {}
        interpreted_prof: dict[str, str | None] = {}

        def accept(index, name, prof, sid, similarity, contains=None) -> None:
            if sid in resolved:  # the student already has it as a confirmed skill
                warnings[index] = None
                return
            if prof not in PROFICIENCY_ORDER:
                prof = None
            known = interpreted.get(sid)
            if known and known.similarity >= similarity:
                warnings[index] = None
                return
            if known:
                warnings[known.warning_index] = None
            interpreted[sid] = Interpretation(name, sid, self.name_of(sid), similarity, index, contains)
            interpreted_prof[sid] = prof
            warnings[index] = interpreted[sid].message()

        pending: list[tuple[int, str, str | None]] = []  # offered to the embedding interpreter
        for index, name, prof in unknown:
            contained = self._contained_skill(name)
            if contained is not None:
                accept(index, name, prof, contained[0], 1.0, contained[1])
                continue
            suggestions = self._suggest(name)
            if suggestions:  # a fragment of a longer skill name: ask, do not guess
                not_held = [sid for sid in suggestions if sid not in resolved]
                if not_held:
                    warnings[index] += " " + self._did_you_mean(not_held)
                continue
            pending.append((index, name, prof))

        if pending and interpreter is not None:
            try:
                results = list(interpreter([name for _, name, _ in pending]))
                if len(results) != len(pending):
                    raise ValueError("interpreter returned the wrong number of results")
            except Exception as exc:  # any failure keeps the old behaviour
                logger.warning("Skill interpretation unavailable (%s): %s", type(exc).__name__, exc)
                results = [None] * len(pending)
            for (index, name, prof), hit in zip(pending, results):
                if hit is not None and self.has(hit[0]):
                    accept(index, name, prof, hit[0], hit[1])
        resolved.update(interpreted_prof)
        return resolved, [w for w in warnings if w is not None], interpreted

    def _contained_skill(self, text: str) -> tuple[str, str] | None:
        """(skill_id, matched phrase) if exactly one catalogue skill appears in `text` as a
        whole phrase ("Python (pandas)", "Advanced Excel"); None if none or several do."""
        lowered = text.lower()
        found: dict[str, str] = {}
        for (pattern, sid), (phrase, _) in zip(self._phrases, self._phrase_texts):
            if pattern.search(lowered) and len(phrase) > len(found.get(sid, "")):
                found[sid] = phrase
        if len(found) != 1:
            return None
        ((sid, phrase),) = found.items()
        return sid, phrase

    def _suggest(self, text: str) -> list[str]:
        """Skill_ids whose name or alias has `text` as a strict part of it, by whole words
        ("Accounting" is part of "Accounting Software"). At most 3, else none (too vague)."""
        words = _WORDS.findall(text.lower())
        if not words or len("".join(words)) < 3:
            return []
        found: set[str] = set()
        for phrase, sid in self._phrase_texts:
            target = _WORDS.findall(phrase.lower())
            if len(target) > len(words) and any(
                target[i:i + len(words)] == words for i in range(len(target) - len(words) + 1)
            ):
                found.add(sid)
        return sorted(found, key=self.name_of) if len(found) <= 3 else []

    def _did_you_mean(self, skill_ids: list[str]) -> str:
        names = [self.name_of(sid) for sid in skill_ids]
        if len(names) == 1:
            return f"Did you mean {names[0]}?"
        return f"Did you mean {', '.join(names[:-1])} or {names[-1]}?"

    def find_in_text(self, text: str) -> set[str]:
        """Skill_ids whose name or alias appears as a whole phrase in text."""
        lowered = (text or "").lower()
        return {sid for pattern, sid in self._phrases if pattern.search(lowered)}
