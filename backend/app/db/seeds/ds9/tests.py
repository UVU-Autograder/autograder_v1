import pytest
from python_autograder_helpers import import_student_modules
from student_test_helpers import assert_student_pytest_passes, assert_test_function_count


@pytest.mark.ag_ds8_regression
def test_ds8_regression() -> None:
    (des_mod,) = import_student_modules("dessert")
    Order = des_mod.Order
    order = Order()
    assert order.get_pay_type() == "CASH"
    order.set_pay_type("CARD")
    assert order.get_pay_type() == "CARD"
    order.set_pay_type("PHONE")
    assert order.get_pay_type() == "PHONE"

    with pytest.raises(ValueError):
        order.set_pay_type("INVALID")  # type: ignore


@pytest.mark.ag_relational_ops
def test_relational_ops() -> None:
    (des_mod,) = import_student_modules("dessert")
    Candy = des_mod.Candy
    c1 = Candy("Cheap Candy", 1.0, 2.0)  # cost 2.0
    c2 = Candy("Expensive Candy", 2.0, 2.0)  # cost 4.0
    c3 = Candy("Equal Candy", 1.0, 2.0)  # cost 2.0

    assert c1 < c2
    assert c2 > c1
    assert c1 <= c3
    assert c1 >= c3
    assert c1 == c3
    assert c1 != c2

    # Verify __eq__ handles comparison against non-DessertItem objects gracefully
    assert not (c1 == None)  # noqa: E711
    assert not (c1 == "string")
    assert c1 != None  # noqa: E711
    assert c1 != 123


@pytest.mark.ag_order_sort
def test_order_sort() -> None:
    (des_mod,) = import_student_modules("dessert")
    Candy = des_mod.Candy
    Order = des_mod.Order
    order = Order()
    c1 = Candy("Expensive", 5.0, 2.0)  # cost 10.0
    c2 = Candy("Cheap", 1.0, 1.0)  # cost 1.0
    c3 = Candy("Medium", 2.0, 2.0)  # cost 4.0

    order.add(c1)
    order.add(c2)
    order.add(c3)
    order.sort()

    assert order.order == [c2, c3, c1]


@pytest.mark.ag_student_sort_tests
def test_student_sort_tests() -> None:
    assert_test_function_count("test_order.py", minimum=5)
    assert_student_pytest_passes("test_order.py", minimum=5, timeout_seconds=10)
