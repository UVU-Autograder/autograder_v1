from app.domains.grading.normalizer import (
    compare_exact,
    compare_numeric_tolerance,
    compare_outputs,
    compare_regex,
    normalize_output,
)


def test_normalize_output_basics() -> None:
    raw = "  hello world  \r\n\r\nline two   \n  \n"
    assert normalize_output(raw) == "hello world\nline two"
    assert normalize_output("") == ""
    assert normalize_output(None) == ""


def test_compare_exact() -> None:
    # Identical
    assert compare_exact("foo\nbar", "foo\nbar")
    # CRLF normalized to LF
    assert compare_exact("foo\r\nbar\r\n", "foo\nbar\n")
    # Trailing space matters in exact mode
    assert not compare_exact("foo \nbar", "foo\nbar")
    # Casing matters
    assert not compare_exact("Foo", "foo")
    # Empty strings
    assert compare_exact("", "")
    assert compare_exact(None, "")


def test_compare_regex() -> None:
    # Simple match
    assert compare_regex("Hello 1234 World", r"Hello \d+ World")
    # Non-match
    assert not compare_regex("Hello World", r"Hello \d+ World")
    # MULTILINE mode
    multiline_text = "Header\nStatus: 200 OK\nFooter"
    assert compare_regex(multiline_text, r"^Status: \d+ OK$")
    assert not compare_regex(multiline_text, r"^Status: 404$")
    # Cross-platform CRLF normalization in pattern
    assert compare_regex("line1\nline2", "line1\r\nline2")
    # Empty pattern handling
    assert compare_regex("", "")
    assert compare_regex("", None)
    assert not compare_regex("Traceback: Error", "")
    assert not compare_regex("Traceback: Error", None)
    # Invalid regex syntax does not raise
    assert not compare_regex("text", r"[unclosed-regex")


def test_compare_numeric_tolerance_pure_float() -> None:
    # Default tolerance (1e-4)
    assert compare_numeric_tolerance("3.14159", "3.14160")
    assert not compare_numeric_tolerance("3.14159", "3.14200")

    # Custom tolerance
    assert compare_numeric_tolerance("3.14", "3.15", tolerance=0.02)
    assert not compare_numeric_tolerance("3.14", "3.15", tolerance=0.001)

    # String and negative tolerance fallbacks
    assert compare_numeric_tolerance("3.14", "3.15", tolerance="0.02")
    assert compare_numeric_tolerance("3.14159", "3.14160", tolerance=-0.5)

    # NaN handling
    assert compare_numeric_tolerance("nan", "NaN")

    # Scientific notation
    assert compare_numeric_tolerance("1.0e-4", "0.0001")
    assert compare_numeric_tolerance("-2.5e2", "-250.0")


def test_compare_numeric_tolerance_mixed_text() -> None:
    # Single number with text
    assert compare_numeric_tolerance("Total: $127.15000", "Total: $127.15")
    assert not compare_numeric_tolerance("Total: $127.25", "Total: $127.15")

    # Multiple numbers
    actual = "Point A: 10.00001, Point B: 20.00002\nDistance: 14.14213"
    expected = "Point A: 10.0, Point B: 20.0\nDistance: 14.1421"
    assert compare_numeric_tolerance(actual, expected)

    # Different number count fails
    assert not compare_numeric_tolerance("Val: 1 2 3", "Val: 1 2")

    # Non-numeric difference fails
    assert not compare_numeric_tolerance("Tax: $12.50", "Total: $12.50")


def test_compare_outputs_dispatch() -> None:
    # Normalized (default)
    assert compare_outputs("hello   \nworld", "hello\nworld", mode="normalized")
    assert not compare_outputs("hello world", "goodbye world", mode="normalized")

    # Exact
    assert compare_outputs("data\r\n123", "data\n123", mode="exact")
    assert not compare_outputs("data  \n123", "data\n123", mode="exact")

    # Numeric tolerance
    assert compare_outputs("42.00001", "42.0", mode="numeric_tolerance")
    assert compare_outputs("Score: 99.5", "Score: 100.0", mode="numeric_tolerance", tolerance=0.01)
    assert not compare_outputs("Score: 95.0", "Score: 100.0", mode="numeric_tolerance", tolerance=0.01)

    # Regex
    assert compare_outputs("Timestamp: 2026-11-12", r"Timestamp: \d{4}-\d{2}-\d{2}", mode="regex")
    assert not compare_outputs("Timestamp: invalid", r"Timestamp: \d{4}-\d{2}-\d{2}", mode="regex")

    # Unknown mode falls back to normalized
    assert compare_outputs("  test  \n", "test", mode="unknown_mode")
