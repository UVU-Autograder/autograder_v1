import inspect

import pytest
from python_autograder_helpers import import_student_modules
from student_test_helpers import (
    assert_student_pytest_passes,
    assert_test_function_count,
)

(des_mod,) = import_student_modules("dessert")
DessertItem = getattr(des_mod, "DessertItem", None)
Candy = getattr(des_mod, "Candy", None)
Cookie = getattr(des_mod, "Cookie", None)
IceCream = getattr(des_mod, "IceCream", None)
Sundae = getattr(des_mod, "Sundae", None)
Order = getattr(des_mod, "Order", None)


@pytest.mark.ag_ds2_regression
def test_ds2_regression():
    assert inspect.isclass(DessertItem), "DessertItem must be a class"
    assert inspect.isclass(Order), "Order must be a class"
    assert hasattr(Order, "__len__"), "Order must implement __len__"
    order = Order()
    assert len(order) == 0, "Initial Order length must be 0"
    order.add(DessertItem("Test"))
    assert len(order) == 1, "Order length must be 1 after add()"
    assert issubclass(Candy, DessertItem), "Candy must inherit from DessertItem"
    assert issubclass(Cookie, DessertItem), "Cookie must inherit from DessertItem"
    assert issubclass(IceCream, DessertItem), "IceCream must inherit from DessertItem"
    assert issubclass(Sundae, IceCream), "Sundae must inherit from IceCream"


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
