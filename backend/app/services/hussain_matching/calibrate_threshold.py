"""Suggest a similarity threshold from labelled skill-name pairs.

    python -m services.matching.calibrate_threshold [pairs.json]

Scores every pair in calibration_pairs.json with the real embedding model and
prints a table, then reports how candidate thresholds perform. Labels:
synonyms (should match), unrelated (clearly different) and hard_negatives
(close but different skills that must not match). It only prints; it never
changes scoring.SIMILARITY_THRESHOLD. Needs sentence-transformers.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from . import scoring
from .embeddings import EmbeddingProvider

DEFAULT_PAIRS = Path(__file__).resolve().parent / "calibration_pairs.json"
LABELS = {"synonyms": "synonym", "unrelated": "unrelated", "hard_negatives": "hard_negative"}
CHECK_THRESHOLDS = (0.45, 0.50, 0.55, 0.60)
MIN_SYNONYMS_KEPT = 12


def score_pairs(data: dict, provider_factory=EmbeddingProvider) -> list[tuple[float, str, str, str]]:
    """Return [(score, label, a, b)] for every labelled pair, highest score first."""
    labelled = [(label, pair) for key, label in LABELS.items() for pair in data.get(key, [])]
    names = sorted({n for _, pair in labelled for n in pair})
    provider = provider_factory({n: n for n in names})  # each skill name is its own id
    rows = [(provider(a, b), label, a, b) for label, (a, b) in labelled]
    return sorted(rows, key=lambda r: -r[0])


def evaluate(rows, threshold: float) -> dict:
    """Counts per label; a synonym is kept at score >= threshold, a negative is rejected below it."""
    def count(label, kept):
        return sum(1 for s, l, *_ in rows if l == label and (s >= threshold) == kept)

    syn_kept, syn_total = count("synonym", True), sum(1 for r in rows if r[1] == "synonym")
    unr_rej, unr_total = count("unrelated", False), sum(1 for r in rows if r[1] == "unrelated")
    hard_rej, hard_total = count("hard_negative", False), sum(1 for r in rows if r[1] == "hard_negative")
    neg_rej, neg_total = unr_rej + hard_rej, unr_total + hard_total
    recall = syn_kept / syn_total if syn_total else 0.0
    specificity = neg_rej / neg_total if neg_total else 0.0
    return {"syn_kept": syn_kept, "syn_total": syn_total, "unr_rej": unr_rej, "unr_total": unr_total,
            "hard_rej": hard_rej, "hard_total": hard_total,
            "balanced_accuracy": (recall + specificity) / 2}


def suggest_threshold(rows) -> float:
    """Threshold maximising balanced accuracy (synonyms vs all negatives). Candidates
    are midpoints between neighbouring scores; ties go to the higher threshold."""
    scores = sorted({round(r[0], 6) for r in rows})
    candidates = [(a + b) / 2 for a, b in zip(scores, scores[1:])] or [scores[0]]
    return max(candidates, key=lambda t: (evaluate(rows, t)["balanced_accuracy"], t))


def lowest_safe_threshold(rows, min_synonyms: int = MIN_SYNONYMS_KEPT):
    """Lowest threshold (rounded up to 0.01) that rejects every negative (unrelated
    and hard) and keeps at least `min_synonyms` synonyms. Returns
    (threshold, highest_negative, nth_best_synonym), or None if impossible."""
    negatives = [s for s, l, *_ in rows if l != "synonym"]
    synonyms = sorted((s for s, l, *_ in rows if l == "synonym"), reverse=True)
    if not negatives or len(synonyms) < min_synonyms:
        return None
    floor, ceiling = max(negatives), synonyms[min_synonyms - 1]
    threshold = math.floor(floor * 100) / 100 + 0.01
    return (threshold, floor, ceiling) if floor < threshold <= ceiling else None


def _line(label, t, e) -> str:
    return (f"{t:9.3f}  {e['syn_kept']:>3}/{e['syn_total']:<3}      {e['unr_rej']:>3}/{e['unr_total']:<3}"
            f"        {e['hard_rej']:>3}/{e['hard_total']:<3}       {e['balanced_accuracy']:5.0%}   {label}")


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_PAIRS
    rows = score_pairs(json.loads(path.read_text(encoding="utf-8")))

    print(f"{'score':>6}  {'label':<13} pair")
    for score, label, a, b in rows:
        print(f"{score:6.3f}  {label:<13} {a} <-> {b}")

    print()
    for label in ("synonym", "unrelated", "hard_negative"):
        v = sorted(s for s, l, *_ in rows if l == label)
        print(f"{label + ':':<15} min {v[0]:.3f}  median {v[len(v) // 2]:.3f}  max {v[-1]:.3f}")

    suggested = suggest_threshold(rows)
    print(f"\n{'threshold':>9}  synonyms kept  unrelated rejected  hard rejected  bal.acc")
    for label, t in [("current", scoring.SIMILARITY_THRESHOLD), *[("", t) for t in CHECK_THRESHOLDS],
                     ("best balanced accuracy", suggested)]:
        print(_line(label, t, evaluate(rows, t)))

    safe = lowest_safe_threshold(rows)
    print(f"\nRule: lowest threshold that rejects every negative and keeps >= {MIN_SYNONYMS_KEPT} synonyms.")
    if safe:
        t, floor, ceiling = safe
        print(f"Result: {t:.2f}  (valid range: above {floor:.3f}, up to {ceiling:.3f}).")
    else:
        print("Result: NONE. No threshold rejects every negative and keeps that many synonyms.")
    print(f"SIMILARITY_THRESHOLD is {scoring.SIMILARITY_THRESHOLD}; not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
