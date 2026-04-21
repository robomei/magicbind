"""Integration tests: full build and import."""
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


def test_to_map(math_utils):
    result = math_utils.to_map(["a", "b", "c"], [1.0, 2.0, 3.0])
    assert result == {"a": 1.0, "b": 2.0, "c": 3.0}


def test_map_sum(math_utils):
    assert math_utils.map_sum({"a": 1.0, "b": 2.0, "c": 3.0}) == 6.0


def test_unique_ints(math_utils):
    result = math_utils.unique_ints([3, 1, 2, 1, 3])
    assert result == {1, 2, 3}


def test_set_size(math_utils):
    assert math_utils.set_size({1, 2, 3, 4}) == 4


def test_first_three(math_utils):
    result = math_utils.first_three([10.0, 20.0, 30.0, 40.0])
    assert list(result) == [10.0, 20.0, 30.0]


def test_classify_int(math_utils):
    assert math_utils.classify(3.0) == 3


def test_classify_double(math_utils):
    assert math_utils.classify(3.5) == 3.5


def test_classify_large(math_utils):
    assert math_utils.classify(9999.5) == "large"


def test_complex_mul(math_utils):
    result = math_utils.complex_mul(complex(1, 2), complex(3, 4))
    assert result == complex(1, 2) * complex(3, 4)


def test_count_chars(math_utils):
    result = math_utils.count_chars("hello")
    assert result["l"] == 2
    assert result["h"] == 1


def test_file_extension(math_utils):
    assert math_utils.file_extension("image.png") == ".png"


def test_string_length(math_utils):
    assert math_utils.string_length("hello") == 5


def test_safe_divide(math_utils):
    assert math_utils.safe_divide(10.0, 2.0) == 5.0


def test_safe_divide_by_zero(math_utils):
    with pytest.raises(ValueError, match="division by zero"):
        math_utils.safe_divide(1.0, 0.0)


def test_get_element(math_utils):
    assert math_utils.get_element([1.0, 2.0, 3.0], 1) == 2.0


def test_get_element_out_of_range(math_utils):
    with pytest.raises(IndexError):
        math_utils.get_element([1.0, 2.0], 5)


def test_invalid_module_name(tmp_path_factory):
    work = tmp_path_factory.mktemp("invalid_name")
    r = subprocess.run(
        [sys.executable, "-m", "magicbind.cli", "add", str(MATH_HEADER), "--module", "bad-name"],
        capture_output=True, text=True, cwd=work,
    )
    assert r.returncode != 0
    assert "valid Python identifier" in r.stderr


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
