"""Embedding similarity for skills (plugs into Matcher's `similarity` hook).

    provider = EmbeddingProvider.from_catalogue(catalogue, cache_path="emb.json")
    matcher = Matcher(normalizer, similarity=provider)

The provider is called with two skill_ids and returns a similarity. Each skill's
name and every alias are embedded separately; the similarity of two skills is
the highest cosine over all their text pairs. Embeddings are computed once (one
batch), kept in memory and optionally saved to a JSON cache that is invalidated
per skill when the model or the skill's texts change.

sentence-transformers is imported lazily, so this module imports without it.
Skill pairs listed under the catalogue's optional "not_equivalent" key
(`[["java", "javascript"], ...]`) always return 0: they are known to be close
but different, which names alone cannot tell apart.

`interpret(texts)` maps free text that is not in the catalogue to the closest skill
(see Matcher: it is credited as a partial, unconfirmed match).

Pass `model=` (anything with `.encode(list[str])`) to use a different or fake model.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .normalizer import Ambiguous
from .scoring import SIMILARITY_THRESHOLD

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_QUERY_CHARS = 200  # same limit as the RunPod worker
MAX_QUERY_CACHE = 1000  # free texts kept in memory
AMBIGUITY_MARGIN = 0.03  # best and second-best candidate this close: do not pick one


def _normalize(vec: Iterable[float]) -> list[float]:
    values = [float(x) for x in vec]
    norm = math.sqrt(sum(x * x for x in values))
    return [x / norm for x in values] if norm else values


def skill_texts(skill: dict) -> list[str]:
    """Texts embedded for a skill: its name, then each alias."""
    return [skill["name"], *skill.get("aliases", [])]


class EmbeddingProvider:
    def __init__(
        self,
        texts_by_skill: Mapping[str, str | Sequence[str]],
        *,
        model_name: str = DEFAULT_MODEL,
        model=None,
        cache_path: str | Path | None = None,
        not_equivalent: Iterable[Sequence[str]] = (),
    ):
        self.model_name = model_name
        # skill_id -> texts that are embedded (a single string counts as one text)
        self._texts: dict[str, list[str]] = {
            sid: [t] if isinstance(t, str) else list(t) for sid, t in texts_by_skill.items()
        }
        self._not_equivalent: set[frozenset[str]] = set()
        for pair in not_equivalent:
            ids = list(pair)
            if len(ids) != 2 or ids[0] == ids[1]:
                raise ValueError(f"not_equivalent entries must be two different skill_ids: {ids}")
            unknown = [i for i in ids if i not in self._texts]
            if unknown:
                raise ValueError(f"not_equivalent refers to unknown skill_id(s): {unknown}")
            self._not_equivalent.add(frozenset(ids))
        self._model = model
        self._cache_path = Path(cache_path) if cache_path else None
        self._vectors: dict[str, list[list[float]]] = {}
        self._query_vectors: dict[str, list[float]] = {}  # free text -> vector (in memory only)
        self._load_cache()

    @classmethod
    def from_skills(cls, skills: list[dict], **kwargs) -> "EmbeddingProvider":
        """Build from catalogue entries `{skill_id, name, aliases[]}`."""
        return cls({s["skill_id"]: skill_texts(s) for s in skills}, **kwargs)

    @classmethod
    def from_catalogue(cls, catalogue: dict, **kwargs) -> "EmbeddingProvider":
        """Build from a catalogue dict `{"skills": [...], "not_equivalent": [[id, id], ...]}`."""
        return cls.from_skills(
            catalogue["skills"], not_equivalent=catalogue.get("not_equivalent", []), **kwargs
        )

    def precompute(self) -> None:
        """Embed every skill not already cached. Safe to call repeatedly."""
        missing = [sid for sid in self._texts if sid not in self._vectors]
        if not missing:
            return
        flat = [t for sid in missing for t in self._texts[sid]]
        encoded = iter(self._get_model().encode(flat))
        for sid in missing:
            self._vectors[sid] = [_normalize(next(encoded)) for _ in self._texts[sid]]
        self._save_cache()

    def __call__(self, skill_a: str, skill_b: str) -> float:
        """Max cosine over all text pairs of two skills. 0.0 if either skill_id is
        unknown or the pair is listed as not equivalent."""
        if skill_a not in self._texts or skill_b not in self._texts:
            return 0.0
        if frozenset((skill_a, skill_b)) in self._not_equivalent:
            return 0.0
        self.precompute()
        best = max(
            sum(x * y for x, y in zip(va, vb))
            for va in self._vectors[skill_a]
            for vb in self._vectors[skill_b]
        )
        return max(-1.0, min(1.0, best))

    def interpret(
        self, texts: Sequence[str], *, threshold: float = SIMILARITY_THRESHOLD
    ) -> list[tuple[str, float] | Ambiguous | None]:
        """Map free text (not a skill_id) to the closest catalogue skill.

        One entry per input: (skill_id, similarity) when the best max-cosine over
        that skill's name and aliases is >= threshold, else None. Two cases are rejected
        as ambiguous instead of guessed: the best skill and another skill that passes
        the threshold form a `not_equivalent` pair (None; a raw text has no skill_id of
        its own, so the list can only be applied to the candidates), or the two best
        skills that pass the threshold are within AMBIGUITY_MARGIN of each other
        (`Ambiguous`, so the caller can ask "did you mean X or Y?"). Blank text gives None.
        """
        cleaned = [(t or "").strip()[:MAX_QUERY_CHARS] for t in texts]
        self.precompute()
        vectors = self._embed_queries([t for t in cleaned if t])
        return [self._nearest(vectors[t], threshold) if t else None for t in cleaned]

    def _embed_queries(self, texts: Sequence[str]) -> dict[str, list[float]]:
        """Normalised vectors for free texts; one model call for the uncached ones."""
        todo = list(dict.fromkeys(t for t in texts if t not in self._query_vectors))
        fresh: dict[str, list[float]] = {}
        if todo:
            encoded = list(self._get_model().encode(todo))
            if len(encoded) != len(todo):
                raise ValueError("embedding model returned the wrong number of vectors")
            fresh = {text: _normalize(vec) for text, vec in zip(todo, encoded)}
            for text, vec in fresh.items():
                if len(self._query_vectors) < MAX_QUERY_CACHE:
                    self._query_vectors[text] = vec
        return {t: self._query_vectors.get(t) or fresh[t] for t in texts}

    def _nearest(self, vec: list[float], threshold: float) -> tuple[str, float] | Ambiguous | None:
        scored = sorted(
            (
                (max(sum(x * y for x, y in zip(vec, v)) for v in vectors), sid)
                for sid, vectors in self._vectors.items()
            ),
            key=lambda item: (-item[0], item[1]),
        )
        passing = [(min(1.0, s), sid) for s, sid in scored if s >= threshold]
        if not passing:
            return None
        best_score, best_id = passing[0]
        if any(frozenset((best_id, sid)) in self._not_equivalent for _, sid in passing[1:]):
            return None
        if len(passing) > 1 and best_score - passing[1][0] <= AMBIGUITY_MARGIN + 1e-9:
            return Ambiguous(((best_id, best_score), (passing[1][1], passing[1][0])))
        return best_id, best_score

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "EmbeddingProvider needs sentence-transformers: "
                    "pip install sentence-transformers"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _load_cache(self) -> None:
        if not (self._cache_path and self._cache_path.exists()):
            return
        try:
            data = json.loads(self._cache_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return  # unreadable cache: recompute
        if data.get("model") != self.model_name:
            return
        texts, vectors = data.get("texts", {}), data.get("vectors", {})
        for sid, current in self._texts.items():
            if texts.get(sid) == current and len(vectors.get(sid, [])) == len(current):
                self._vectors[sid] = vectors[sid]

    def _save_cache(self) -> None:
        if not self._cache_path:
            return
        payload = {
            "model": self.model_name,
            "texts": {sid: self._texts[sid] for sid in self._vectors},
            "vectors": self._vectors,
        }
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._cache_path.with_suffix(self._cache_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(self._cache_path)
