from app.domains.assignments.io_parser import extract_expected_io


def test_extract_expected_io_basic_constants() -> None:
    source_code = """
import pytest

EXPECTED_INPUT = "hello"
EXPECTED_OUTPUT = "world"

@pytest.mark.ag_greeting
def test_greeting():
    pass
"""
    results = extract_expected_io(source_code)
    assert "ag_greeting" in results
    assert results["ag_greeting"]["expected_input"] == "hello"
    assert results["ag_greeting"]["expected_output"] == "world"


def test_extract_expected_io_annotated_assignments() -> None:
    source_code = """
import pytest

EXPECTED_INPUT: str = "ann input"
EXPECTED_OUTPUT: str = "ann output"

@pytest.mark.ag_annotated
def test_annotated():
    pass
"""
    results = extract_expected_io(source_code)
    assert "ag_annotated" in results
    assert results["ag_annotated"]["expected_input"] == "ann input"
    assert results["ag_annotated"]["expected_output"] == "ann output"


def test_extract_expected_io_empty_string_constants() -> None:
    source_code = """
import pytest

EXPECTED_OUTPUT = ""

@pytest.mark.ag_empty
def test_empty():
    EXPECTED_OUTPUT = ""
"""
    results = extract_expected_io(source_code)
    assert "ag_empty" in results
    assert results["ag_empty"]["expected_output"] == ""


def test_extract_expected_io_function_scoped_overrides() -> None:
    source_code = """
import pytest

EXPECTED_INPUT = "global input"
EXPECTED_OUTPUT = "global output"

@pytest.mark.ag_test_one
def test_one():
    EXPECTED_INPUT = "func input"
    EXPECTED_OUTPUT = "func output"
    pass

@pytest.mark.ag_test_two
def test_two():
    pass
"""
    results = extract_expected_io(source_code)
    assert results["ag_test_one"]["expected_input"] == "func input"
    assert results["ag_test_one"]["expected_output"] == "func output"
    assert results["ag_test_two"]["expected_input"] == "global input"
    assert results["ag_test_two"]["expected_output"] == "global output"


def test_extract_expected_io_multiple_markers() -> None:
    source_code = """
import pytest

@pytest.mark.ag_part_a
@pytest.mark.ag_part_b
def test_combined():
    EXPECTED_OUTPUT = "42"
"""
    results = extract_expected_io(source_code)
    assert results["ag_part_a"]["expected_output"] == "42"
    assert results["ag_part_b"]["expected_output"] == "42"


def test_extract_expected_io_syntax_error() -> None:
    source_code = "def invalid_syntax(:"
    results = extract_expected_io(source_code)
    assert results == {}


def test_extract_expected_io_comparison_modes_and_tolerance() -> None:
    source_code = """
import pytest

COMPARISON_MODE = "exact"
TOLERANCE = 0.01

@pytest.mark.ag_exact_test
def test_exact():
    EXPECTED_OUTPUT = "exact\\nformat"

@pytest.mark.ag_override_mode
def test_override():
    COMPARISON_MODE = "numeric_tolerance"
    TOLERANCE = 0.0005
    EXPECTED_OUTPUT = "3.14159"

@pytest.mark.ag_regex_test
def test_regex():
    COMPARISON_MODE = "regex"
    EXPECTED_OUTPUT = r"^Hello \\d+$"
"""
    results = extract_expected_io(source_code)
    assert results["ag_exact_test"]["comparison_mode"] == "exact"
    assert results["ag_exact_test"]["tolerance"] == 0.01
    assert results["ag_exact_test"]["expected_output"] == "exact\nformat"

    assert results["ag_override_mode"]["comparison_mode"] == "numeric_tolerance"
    assert results["ag_override_mode"]["tolerance"] == 0.0005
    assert results["ag_override_mode"]["expected_output"] == "3.14159"

    assert results["ag_regex_test"]["comparison_mode"] == "regex"
    assert results["ag_regex_test"]["tolerance"] == 0.01
    assert results["ag_regex_test"]["expected_output"] == r"^Hello \d+$"


def test_extract_expected_io_annotated_mode_and_tolerance() -> None:
    source_code = """
import pytest

@pytest.mark.ag_annotated_mode
def test_annotated():
    COMPARISON_MODE: str = "exact"
    TOLERANCE: float = 1e-5
    EXPECTED_OUTPUT: str = "ok"
"""
    results = extract_expected_io(source_code)
    assert results["ag_annotated_mode"]["comparison_mode"] == "exact"
    assert results["ag_annotated_mode"]["tolerance"] == 1e-5
    assert results["ag_annotated_mode"]["expected_output"] == "ok"

