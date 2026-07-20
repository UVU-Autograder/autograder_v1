import pytest
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
