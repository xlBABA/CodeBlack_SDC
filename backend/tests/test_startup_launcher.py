"""Tests for start.py's pure config-resolution helpers. Does not actually
launch a server — uvicorn.run() is only imported inside main(), which
these tests never call."""
import sys
from pathlib import Path

import pytest

# start.py lives at the backend/ root, not inside the app package — add it
# to sys.path the same way `python start.py` would find it as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from start import resolve_port, should_reload  # noqa: E402


def test_resolve_port_defaults_to_8000_when_unset():
    assert resolve_port(env={}) == 8000


def test_resolve_port_reads_platform_provided_port():
    assert resolve_port(env={"PORT": "3000"}) == 3000


def test_resolve_port_rejects_non_integer_value():
    with pytest.raises(ValueError):
        resolve_port(env={"PORT": "not-a-number"})


@pytest.mark.parametrize("port", [1, 65535, 8000, 3000])
def test_resolve_port_accepts_valid_boundary_and_typical_values(port):
    assert resolve_port(env={"PORT": str(port)}) == port


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_resolve_port_rejects_out_of_range_values(port):
    with pytest.raises(ValueError):
        resolve_port(env={"PORT": str(port)})


# --- should_reload: must fail safe unless ENVIRONMENT is explicitly
# "development" — never by an implicit default. ----------------------------


def test_should_reload_true_when_explicitly_development():
    assert should_reload(env={"ENVIRONMENT": "development"}) is True


def test_should_reload_false_when_environment_is_unset():
    assert should_reload(env={}) is False


def test_should_reload_false_when_environment_is_empty_string():
    assert should_reload(env={"ENVIRONMENT": ""}) is False


def test_should_reload_false_for_production():
    assert should_reload(env={"ENVIRONMENT": "production"}) is False


@pytest.mark.parametrize(
    "environment", ["production", "staging", "replit", "", "Development", "DEVELOPMENT", "dev"]
)
def test_should_reload_false_for_anything_other_than_exact_development(environment):
    assert should_reload(env={"ENVIRONMENT": environment}) is False
