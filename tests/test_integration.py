"""Integration tests: full build and import."""
import importlib
import subprocess
import sys
from pathlib import Path

import pytest


FIXTURES = Path(__file__).parent / "fixtures"
MATH_HEADER = FIXTURES / "math_utils.h"
MATH_SOURCE = FIXTURES / "math_utils.cpp"


@pytest.fixture(scope="module")
def math_utils(tmp_path_factory):
    """Build and import math_utils from the test fixtures."""
    work = tmp_path_factory.mktemp("integration")
    result = subprocess.run(
        [
            sys.executable, "-m", "magicbind.cli", "add",
            str(MATH_HEADER),
            "--source", str(MATH_SOURCE),
        ],
        capture_output=True, text=True, cwd=work,
    )
    assert result.returncode == 0, result.stderr + result.stdout

    import math_utils
    importlib.reload(math_utils)
    return math_utils


def test_sum(math_utils):
    assert math_utils.sum([1.0, 2.0, 3.0]) == 6.0


def test_sum_empty(math_utils):
    assert math_utils.sum([]) == 0.0


def test_mean(math_utils):
    assert math_utils.mean([1.0, 2.0, 3.0]) == 2.0


def test_mean_empty_returns_none(math_utils):
    assert math_utils.mean([]) is None


def test_clamp_above(math_utils):
    assert math_utils.clamp(10.0, 0.0, 5.0) == 5.0


def test_clamp_below(math_utils):
    assert math_utils.clamp(-1.0, 0.0, 5.0) == 0.0


def test_clamp_within(math_utils):
    assert math_utils.clamp(3.0, 0.0, 5.0) == 3.0


def test_minmax(math_utils):
    assert math_utils.minmax([3.0, 1.0, 4.0, 1.0, 5.0]) == (1.0, 5.0)


def test_describe_nonempty(math_utils):
    result = math_utils.describe([1.0, 2.0, 3.0])
    assert "n=3" in result
    assert "sum=6" in result


def test_describe_empty(math_utils):
    assert math_utils.describe([]) == "empty"


def test_chunk(math_utils):
    result = math_utils.chunk([1.0, 2.0, 3.0, 4.0, 5.0], 2)
    assert result == [[1.0, 2.0], [3.0, 4.0], [5.0]]


def test_rebuild(tmp_path_factory):
    """magicbind build should succeed without re-specifying flags."""
    work = tmp_path_factory.mktemp("rebuild")
    # First add
    r = subprocess.run(
        [
            sys.executable, "-m", "magicbind.cli", "add",
            str(MATH_HEADER),
            "--source", str(MATH_SOURCE),
        ],
        capture_output=True, text=True, cwd=work,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    # Then rebuild via build command
    r = subprocess.run(
        [sys.executable, "-m", "magicbind.cli", "build", "math_utils"],
        capture_output=True, text=True, cwd=work,
    )
    assert r.returncode == 0, r.stderr + r.stdout
