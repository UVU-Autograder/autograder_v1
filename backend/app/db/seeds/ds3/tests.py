import pytest
import inspect
import io
import sys
import runpy
import ast
from pathlib import Path

# Import student classes
try:
    from dessert import DessertItem, Candy, Cookie, IceCream, Sundae, Order
except ImportError as exc:
    raise AssertionError(f"Could not import classes from dessert.py: {exc}")


@pytest.mark.ag_ds2_regression
def test_ds2_regression():
    # Verify class definitions
    assert inspect.isclass(DessertItem)
    assert inspect.isclass(Candy)
    assert inspect.isclass(Cookie)
    assert inspect.isclass(IceCream)
    assert inspect.isclass(Sundae)
    assert inspect.isclass(Order)

    # Verify Order methods
    order = Order()
    item = DessertItem("Test")
    order.add(item)
    assert len(order) == 1
    assert next(iter(order)) is item

    # Verify main output in dessertshop.py
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf
    try:
        runpy.run_path("dessertshop.py", run_name="__main__")
    except Exception as exc:
        raise AssertionError(f"dessertshop.py execution failed: {exc}")
    finally:
        sys.stdout = old_stdout

    captured = stdout_buf.getvalue()
    lines = [line.strip() for line in captured.strip().splitlines() if line.strip()]
    assert len(lines) >= 7
    names = ["candy corn", "gummy bears", "chocolate chip", "pistachio", "vanilla", "oatmeal"]
    for name in names:
        assert any(name in line.lower() for line in lines), f"Output missing: {name}"
    assert any("6" in line for line in lines)


@pytest.mark.ag_test_file_exists
def test_file_exists():
    # 1. Physical existence check
    test_file = Path("test_dessert.py")
    assert test_file.exists(), "test_dessert.py is missing from submission"
    assert test_file.is_file(), "test_dessert.py must be a file"

    # 2. AST parsing to count test functions
    try:
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception as exc:
        raise AssertionError(f"Could not parse test_dessert.py: {exc}")

    test_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            test_funcs.append(node.name)

    assert len(test_funcs) >= 15, f"test_dessert.py must define at least 15 test functions starting with 'test_'. Found {len(test_funcs)}: {test_funcs}"


@pytest.mark.ag_student_tests_pass
def test_student_tests_pass():
    test_file = Path("test_dessert.py")
    assert test_file.exists(), "test_dessert.py is missing"

    import subprocess
    import re

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "test_dessert.py", "-v"],
            capture_output=True,
            text=True,
            timeout=10
        )
    except subprocess.TimeoutExpired:
        raise AssertionError("Student test suite execution timed out after 10 seconds.")
    except Exception as exc:
        raise AssertionError(f"Running student tests raised an exception: {exc}")

    # Check outcomes
    assert proc.returncode == 0, f"Student tests failed or crashed. Exit code: {proc.returncode}.\nStdout:\n{proc.stdout}\nStderr:\n{proc.stderr}"
    
    # Parse count of passed tests (e.g. "15 passed")
    match = re.search(r"(\d+)\s+passed", proc.stdout)
    passed_count = int(match.group(1)) if match else 0
    
    assert passed_count >= 15, f"Expected at least 15 tests to pass, but only {passed_count} passed.\nPytest Output:\n{proc.stdout}"
