import pytest
import inspect
import io
import sys
import runpy

from ds_test_helpers import safe_import_dessert, assert_ds1_hierarchy, assert_ds2_order

DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()


@pytest.mark.ag_ds1_regression
def test_ds1_regression():
    assert_ds1_hierarchy(DessertItem, Candy, Cookie, IceCream, Sundae)


@pytest.mark.ag_order_class
def test_order_class():
    assert_ds2_order(Order, DessertItem)


@pytest.mark.ag_main_output
def test_main_output():
    # Run the main function in dessertshop.py and capture stdout
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

    assert len(lines) >= 7, f"Expected output to contain at least 7 lines (6 items + 1 count), got {len(lines)}"

    # Check for the 6 required names
    names = ["candy corn", "gummy bears", "chocolate chip", "pistachio", "vanilla", "oatmeal"]
    for name in names:
        assert any(name in line.lower() for line in lines), f"Output is missing expected item: {name}"

    # Check for total count "6" in the output
    assert any("6" in line for line in lines), "Output is missing expected total count of 6 items"
