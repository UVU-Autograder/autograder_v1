import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_ds8_regression
def test_ds8_regression() -> None:
    (des_mod,) = import_student_modules("dessert")
    Order = des_mod.Order
    order = Order()
    assert order.get_pay_type() == "CASH"
    order.set_pay_type("CARD")
    assert order.get_pay_type() == "CARD"


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
    (student_test_mod,) = import_student_modules("test_order")
    test_funcs = [
        name for name, obj in vars(student_test_mod).items()
        if name.startswith("test_") and callable(obj)
    ]
    assert len(test_funcs) >= 5, f"test_order.py must contain at least 5 test functions (found {len(test_funcs)})"
    has_sort_or_op_test = any(
        "sort" in fn or "op" in fn or "lt" in fn or "gt" in fn or "eq" in fn for fn in test_funcs
    )
    assert has_sort_or_op_test, "test_order.py should include test functions for relational operators or sorting"
