"""Milestone 12B-4/12B-5: app.services.skill_not_equivalent_cached —
strict validation for a FUTURE backend/app/data/cached/
skill_not_equivalent.json file (does not exist in this repo yet).

Milestone 12B-5: Jawad explicitly proposed the file's shape as a
top-level JSON OBJECT with one required key, "not_equivalent":

    {"not_equivalent": [["python", "javascript"], ["excel", "vba"]]}

— superseding the bare-top-level-array shape this loader assumed before
his proposal. These tests exercise that object envelope exclusively.

This module is deliberately NOT wired into careers.py/
HussainMatchingProvider (see the module's own docstring) — these tests
only exercise the isolated loader itself, never production matching.
Every "valid" fixture pair used below is built from skill_ids that are
genuinely present in the real, committed app/data/cached/skills.json
(sql, python) — never an invented skill_id.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.role_catalog_cached import CachedCatalogError
from app.services.skill_not_equivalent_cached import load_skill_not_equivalent_pairs


def _set_path(monkeypatch, path: Path) -> None:
    import app.services.skill_not_equivalent_cached as module

    monkeypatch.setattr(module, "_SKILL_NOT_EQUIVALENT_PATH", path)


def _write(path: Path, data) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _envelope(pairs: list) -> dict:
    return {"not_equivalent": pairs}


# --- Missing file: safe empty list, never an error, never invented data ----


def test_missing_file_resolves_to_empty_list(monkeypatch, tmp_path: Path):
    _set_path(monkeypatch, tmp_path / "does_not_exist.json")
    assert load_skill_not_equivalent_pairs() == []


# --- Valid data loads unchanged ---------------------------------------------


def test_valid_pairs_in_the_object_envelope_load_unchanged(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "python"]]))
    _set_path(monkeypatch, path)

    assert load_skill_not_equivalent_pairs() == [["sql", "python"]]


def test_empty_inner_array_loads_as_empty_list(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([]))
    _set_path(monkeypatch, path)

    assert load_skill_not_equivalent_pairs() == []


# --- Malformed JSON syntax: propagates unwrapped, never silently skipped ---


def test_malformed_json_syntax_raises_json_decode_error(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    path.write_text("{not valid json", encoding="utf-8")
    _set_path(monkeypatch, path)

    with pytest.raises(json.JSONDecodeError):
        load_skill_not_equivalent_pairs()


# --- Structurally invalid top-level shape (object envelope required) -------


def test_bare_top_level_array_is_rejected(monkeypatch, tmp_path: Path):
    """The pre-12B-5 assumption (a bare array) is now superseded by
    Jawad's explicit object-envelope proposal — must be rejected, not
    silently accepted as if it were the old shape."""
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, [["sql", "python"]])
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="top-level JSON object"):
        load_skill_not_equivalent_pairs()


def test_other_non_object_top_level_types_are_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, "not_equivalent")
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="top-level JSON object"):
        load_skill_not_equivalent_pairs()


def test_missing_not_equivalent_key_is_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, {})
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="missing required key"):
        load_skill_not_equivalent_pairs()


def test_unknown_top_level_key_is_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, {"not_equivalent": [["sql", "python"]], "notes": "extra field"})
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="unsupported top-level key"):
        load_skill_not_equivalent_pairs()


def test_unknown_top_level_key_instead_of_not_equivalent_is_rejected(monkeypatch, tmp_path: Path):
    """A differently-named key (e.g. a typo, or an older/alternate
    proposal) must not be silently accepted in place of 'not_equivalent'."""
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, {"exclusions": [["sql", "python"]]})
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError) as exc_info:
        load_skill_not_equivalent_pairs()
    message = str(exc_info.value)
    assert "missing required key" in message or "unsupported top-level key" in message


def test_not_equivalent_value_that_is_not_an_array_is_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, {"not_equivalent": {"sql": "python"}})
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="must be a JSON array"):
        load_skill_not_equivalent_pairs()


# --- Invalid data types within a pair ---------------------------------------


@pytest.mark.parametrize(
    "bad_pair",
    [
        "sql",  # a bare string instead of a pair
        ["sql"],  # only one skill_id
        ["sql", "python", "excel"],  # three skill_ids
        [123, "python"],  # non-string id
        ["sql", None],  # non-string id
        ["sql", ""],  # empty-string id
    ],
)
def test_invalid_pair_data_types_are_rejected(monkeypatch, tmp_path: Path, bad_pair):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([bad_pair]))
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError):
        load_skill_not_equivalent_pairs()


def test_a_pair_naming_the_same_skill_id_twice_is_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "sql"]]))
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="two DIFFERENT"):
        load_skill_not_equivalent_pairs()


# --- Unknown skill_id --------------------------------------------------------


def test_unknown_skill_id_is_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "not_a_real_skill_id"]]))
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="unknown skill_id"):
        load_skill_not_equivalent_pairs()


# --- Duplicate pairs ---------------------------------------------------------


def test_exact_duplicate_pair_is_rejected(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "python"], ["sql", "python"]]))
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="duplicate pair"):
        load_skill_not_equivalent_pairs()


def test_reversed_duplicate_pair_is_also_rejected(monkeypatch, tmp_path: Path):
    """["sql","python"] and ["python","sql"] protect the same two skills —
    a reviewer-facing duplicate, not a different exclusion."""
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "python"], ["python", "sql"]]))
    _set_path(monkeypatch, path)

    with pytest.raises(CachedCatalogError, match="duplicate pair"):
        load_skill_not_equivalent_pairs()


# --- Never invents a pair that wasn't in the file ---------------------------


def test_loader_never_returns_a_pair_not_present_in_the_file(monkeypatch, tmp_path: Path):
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "python"]]))
    _set_path(monkeypatch, path)

    pairs = load_skill_not_equivalent_pairs()
    assert pairs == [["sql", "python"]]
    assert all(len(p) == 2 for p in pairs)


def test_loader_returns_only_the_inner_array_not_the_envelope(monkeypatch, tmp_path: Path):
    """Requirement 6: the return value is the validated inner array,
    already in HussainMatchingProvider's expected list[list[str]] shape
    — never the {"not_equivalent": [...]} wrapper itself."""
    path = tmp_path / "skill_not_equivalent.json"
    _write(path, _envelope([["sql", "python"]]))
    _set_path(monkeypatch, path)

    result = load_skill_not_equivalent_pairs()
    assert result == [["sql", "python"]]
    assert isinstance(result, list)
    assert not isinstance(result, dict)


# --- Wired into production matching (Milestone 13B-8) ----------------------


def test_module_is_now_wired_into_careers_endpoint():
    """Milestone 13B-8: Jawad's real skill_not_equivalent.json has landed
    and is reviewed, so this loader is now wired into
    HussainMatchingProvider via careers.py's _get_shared_hussain_provider()
    — see test_skill_exclusions_matching.py for the actual
    enforcement/fallback/exact-match regression coverage. This test only
    pins the wiring point itself: the loader's name must appear in
    careers.py's namespace (previously asserted absent, before Jawad's
    file existed)."""
    import app.api.v1.endpoints.careers as careers_module

    assert "load_skill_not_equivalent_pairs" in vars(careers_module)
