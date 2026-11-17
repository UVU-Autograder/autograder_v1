"""Regression tests for non-executing rubric metadata synchronization from a Python suite."""
from __future__ import annotations

import pytest

from app.domains.assignments.test_sync import synchronize_python_suite


def _items(source: str) -> dict:
    return {item.key: item for item in synchronize_python_suite(source).items}


# --- comparison-setting scope -------------------------------------------------


def test_function_local_settings_override_module_defaults():
    items = _items(
        "COMPARISON_MODE = 'normalized'\n"
        "TOLERANCE = 0.5\n"
        "@pytest.mark.ag_local\n"
        "def test_local():\n"
        "    COMPARISON_MODE = 'numeric_tolerance'\n"
        "    TOLERANCE = 0.001\n"
        "@pytest.mark.ag_defaulted\n"
        "def test_defaulted():\n"
        "    pass\n"
    )
    assert items["local"].comparison_mode == "numeric_tolerance"
    assert items["local"].tolerance == 0.001
    assert items["defaulted"].comparison_mode == "normalized"
    assert items["defaulted"].tolerance == 0.5


def test_sibling_tests_do_not_inherit_each_others_settings():
    items = _items(
        "@pytest.mark.ag_first\n"
        "def test_first():\n"
        "    COMPARISON_MODE = 'exact'\n"
        "    TOLERANCE = 2\n"
        "    INPUTS = ['1']\n"
        "    OUTPUTS = ['one']\n"
        "@pytest.mark.ag_second\n"
        "def test_second():\n"
        "    pass\n"
    )
    assert items["first"].comparison_mode == "exact"
    assert items["first"].tolerance == 2.0
    second = items["second"]
    assert second.comparison_mode is None
    assert second.tolerance is None
    assert second.inputs is None and second.outputs is None
    assert second.model_fields_set == {"key"}


def test_class_scope_is_inherited_only_by_its_own_methods():
    items = _items(
        "class TestA:\n"
        "    COMPARISON_MODE = 'regex'\n"
        "    @pytest.mark.ag_in_class\n"
        "    def test_in_class(self):\n"
        "        pass\n"
        "@pytest.mark.ag_outside\n"
        "def test_outside():\n"
        "    pass\n"
    )
    assert items["in_class"].comparison_mode == "regex"
    assert items["outside"].comparison_mode is None


def test_missing_settings_stay_absent_rather_than_defaulting():
    result = synchronize_python_suite("@pytest.mark.ag_plain\ndef test_plain():\n    pass\n")
    item = result.items[0]
    assert item.key == "plain"
    assert item.model_fields_set == {"key"}
    assert result.model_dump(exclude_unset=True) == {"items": [{"key": "plain"}]}


def test_non_literal_values_are_not_guessed_or_executed():
    item = _items(
        "@pytest.mark.ag_calc\n"
        "def test_calc():\n"
        "    TOLERANCE = 1 + __import__('os').getpid()\n"
    )["calc"]
    assert item.tolerance is None


def test_same_key_with_conflicting_declarations_is_rejected():
    with pytest.raises(ValueError, match="conflicting comparison_mode"):
        synchronize_python_suite(
            "@pytest.mark.ag_dup\n"
            "def test_one():\n"
            "    COMPARISON_MODE = 'exact'\n"
            "@pytest.mark.ag_dup\n"
            "def test_two():\n"
            "    COMPARISON_MODE = 'regex'\n"
        )


def test_same_key_with_identical_declarations_merges():
    item = _items(
        "@pytest.mark.ag_dup\n"
        "def test_one():\n"
        "    COMPARISON_MODE = 'exact'\n"
        "@pytest.mark.ag_dup\n"
        "def test_two():\n"
        "    COMPARISON_MODE = 'exact'\n"
    )["dup"]
    assert item.comparison_mode == "exact"


@pytest.mark.parametrize("body, message", [
    ("COMPARISON_MODE = 'fuzzy'", "Unsupported comparison mode"),
    ("TOLERANCE = -1", "finite nonnegative"),
    ("TOLERANCE = float('nan')", None),  # not a literal: ignored, never an error
    ("TOLERANCE = True", "finite nonnegative"),
    ("INPUTS = ['1']", "requires both expected input and output"),
    ("INPUTS = ['1', '2']\n    OUTPUTS = ['1']", "unequal input/output counts"),
    ("INPUTS = [1]\n    OUTPUTS = ['1']", "must contain strings"),
])
def test_invalid_settings_are_rejected(body, message):
    source = f"@pytest.mark.ag_bad\ndef test_bad():\n    {body}\n"
    if message is None:
        assert synchronize_python_suite(source).items[0].tolerance is None
        return
    with pytest.raises(ValueError, match=message):
        synchronize_python_suite(source)


def test_syntax_error_and_bad_marker_keys_are_rejected():
    with pytest.raises(ValueError, match="Invalid Python syntax"):
        synchronize_python_suite("def broken(:\n")
    with pytest.raises(ValueError, match="lowercase keys"):
        synchronize_python_suite("@pytest.mark.ag_Bad\ndef test_bad():\n    pass\n")


# --- exact-output whitespace --------------------------------------------------


def test_exact_literals_preserve_trailing_newlines_empty_strings_and_escapes():
    item = _items(
        "@pytest.mark.ag_exact\n"
        "def test_exact():\n"
        "    COMPARISON_MODE = 'exact'\n"
        "    INPUTS = ['', 'a\\n', ' padded ']\n"
        "    OUTPUTS = ['hello\\n', '', 'tab\\there\\n\\n']\n"
    )["exact"]
    assert item.inputs == ["", "a\n", " padded "]
    assert item.outputs == ["hello\n", "", "tab\there\n\n"]


def test_escaped_backslashes_stay_literal_and_are_not_double_decoded():
    item = _items(
        "@pytest.mark.ag_escape\n"
        "def test_escape():\n"
        "    INPUTS = [r'C:\\new']\n"
        "    OUTPUTS = ['back\\\\slash\\\\n']\n"
    )["escape"]
    assert item.inputs == ["C:\\new"]
    assert item.outputs == ["back\\slash\\n"]


def test_single_string_literal_is_wrapped_without_stripping():
    item = _items(
        "@pytest.mark.ag_one\n"
        "def test_one():\n"
        "    INPUT = '3\\n'\n"
        "    OUTPUT = '6\\n'\n"
    )["one"]
    assert item.inputs == ["3\n"]
    assert item.outputs == ["6\n"]


def test_triple_quoted_literals_keep_leading_and_trailing_whitespace():
    item = _items(
        "@pytest.mark.ag_block\n"
        "def test_block():\n"
        "    INPUTS = ['x']\n"
        "    OUTPUTS = ['''  line one\n"
        "line two\n"
        "''']\n"
    )["block"]
    assert item.outputs == ["  line one\nline two\n"]
