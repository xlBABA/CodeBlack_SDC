"""Calibration script logic and pairs file (no model needed)."""
import json
from pathlib import Path

from services.matching.calibrate_threshold import (
    DEFAULT_PAIRS, evaluate, lowest_safe_threshold, score_pairs, suggest_threshold,
)

ROWS = (
    [(s, "synonym", "a", "b") for s in (0.95, 0.9, 0.8, 0.7, 0.6)]
    + [(s, "hard_negative", "c", "d") for s in (0.5, 0.4)]
    + [(s, "unrelated", "e", "f") for s in (0.2, 0.1)]
)


def test_pairs_file_has_labelled_groups_and_no_duplicates():
    data = json.loads(Path(DEFAULT_PAIRS).read_text(encoding="utf-8"))
    assert len(data["synonyms"]) == 20 and len(data["unrelated"]) == 20
    assert len(data["hard_negatives"]) >= 10
    pairs = [tuple(p) for k in ("synonyms", "unrelated", "hard_negatives") for p in data[k]]
    assert all(len(p) == 2 and p[0] != p[1] for p in pairs)
    assert len(pairs) == len({frozenset(p) for p in pairs})


def test_score_pairs_labels_and_sorts_descending():
    data = {"synonyms": [["a", "b"]], "unrelated": [["a", "c"]], "hard_negatives": [["a", "d"]]}
    table = {frozenset(("a", "b")): 0.9, frozenset(("a", "c")): 0.1, frozenset(("a", "d")): 0.5}
    rows = score_pairs(data, lambda texts: lambda x, y: table[frozenset((x, y))])
    assert [(r[1], r[0]) for r in rows] == [("synonym", 0.9), ("hard_negative", 0.5), ("unrelated", 0.1)]


def test_evaluate_counts_per_label():
    e = evaluate(ROWS, 0.55)
    assert (e["syn_kept"], e["syn_total"]) == (5, 5)
    assert (e["hard_rej"], e["hard_total"]) == (2, 2)
    assert (e["unr_rej"], e["unr_total"]) == (2, 2)
    assert evaluate(ROWS, 0.85)["syn_kept"] == 2


def test_lowest_safe_threshold_found_when_classes_separate():
    t, floor, ceiling = lowest_safe_threshold(ROWS, min_synonyms=4)
    assert (t, floor, ceiling) == (0.51, 0.5, 0.7)


def test_lowest_safe_threshold_none_when_hard_negative_beats_synonyms():
    rows = ROWS + [(0.75, "hard_negative", "x", "y")]
    assert lowest_safe_threshold(rows, min_synonyms=4) is None
    assert lowest_safe_threshold(rows, min_synonyms=3)[0] == 0.76


def test_suggest_threshold_separates_clean_data():
    assert 0.5 < suggest_threshold(ROWS) < 0.6
