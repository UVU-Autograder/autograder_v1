import pytest

from ds_test_helpers import (
    assert_dessertshop_main_output,
    assert_ds1_hierarchy,
    assert_ds2_order,
    safe_import_dessert,
)
from student_test_helpers import (
    assert_student_pytest_passes,
    assert_test_function_count,
)

DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()


@pytest.mark.ag_ds2_regression
def test_ds2_regression():
    assert_ds1_hierarchy(DessertItem, Candy, Cookie, IceCream, Sundae)
    assert_ds2_order(Order, DessertItem)
    assert_dessertshop_main_output()


@pytest.mark.ag_test_file_exists
def test_file_exists():
    assert_test_function_count("test_dessert.py", minimum=15)


@pytest.mark.ag_student_tests_pass
def test_student_tests_pass():
    assert_student_pytest_passes(
        "test_dessert.py",
        minimum=15,
        timeout_seconds=10,
    )
