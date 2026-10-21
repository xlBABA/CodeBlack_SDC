import shutil
import tempfile
from pathlib import Path

from services.trends.github_client import WindowCount
from services.trends.snapshot import load_snapshot, save_snapshot, snapshot_path


def _window(count: int) -> WindowCount:
    return WindowCount(topic="sql", start="2026-09-21", end="2026-10-21", total_count=count,
                       incomplete=False, retrieved_at="2026-10-21T12:00:00Z")


def test_load_snapshot_returns_none_when_missing():
    tmp = Path(tempfile.mkdtemp())
    try:
        assert load_snapshot("sql", base_dir=tmp) is None
    finally:
        shutil.rmtree(tmp)


def test_save_then_load_roundtrips_exactly():
    tmp = Path(tempfile.mkdtemp())
    try:
        current = _window(130)
        previous = _window(100)
        save_snapshot("sql", current, previous, base_dir=tmp)
        loaded_current, loaded_previous = load_snapshot("sql", base_dir=tmp)
        assert loaded_current == current
        assert loaded_previous == previous
    finally:
        shutil.rmtree(tmp)


def test_save_creates_parent_directory():
    tmp = Path(tempfile.mkdtemp()) / "nested" / "dir"
    try:
        save_snapshot("sql", _window(1), None, base_dir=tmp)
        assert snapshot_path("sql", base_dir=tmp).exists()
    finally:
        shutil.rmtree(tmp.parent.parent)


def test_snapshot_handles_missing_previous_window():
    tmp = Path(tempfile.mkdtemp())
    try:
        save_snapshot("sql", _window(130), None, base_dir=tmp)
        current, previous = load_snapshot("sql", base_dir=tmp)
        assert current == _window(130)
        assert previous is None
    finally:
        shutil.rmtree(tmp)
