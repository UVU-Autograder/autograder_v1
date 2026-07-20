import pytest
from ds_test_helpers import (
    safe_import_dessert,
    import_student_modules,
)


@pytest.mark.ag_ds7_regression
def test_ds7_regression():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    c = Candy("Fudge", 1.0, 2.0)
    co = Cookie("Choc Chip", 12, 5.0)
    i = IceCream("Vanilla", 2, 1.5)
    s = Sundae("Banana Split", 3, 2.0, "Hot Fudge", 1.0)
    assert c.packaging == "Bag"
    assert co.packaging == "Box"
    assert i.packaging == "Bowl"
    assert s.packaging == "Boat"


@pytest.mark.ag_payment_protocol
def test_payment_protocol():
    (pay_mod,) = import_student_modules("payment")
    Payable = getattr(pay_mod, "Payable", None)
    assert Payable is not None, "Payable Protocol missing in payment.py"
    assert hasattr(Payable, "get_pay_type"), "Payable missing get_pay_type"
    assert hasattr(Payable, "set_pay_type"), "Payable missing set_pay_type"


@pytest.mark.ag_order_payable
def test_order_payable():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    order = Order()
    assert order.get_pay_type() == "CASH"
    order.set_pay_type("CARD")
    assert order.get_pay_type() == "CARD"
    order.set_pay_type("PHONE")
    assert order.get_pay_type() == "PHONE"

    with pytest.raises(ValueError):
        order.set_pay_type("INVALID")  # type: ignore


@pytest.mark.ag_student_order_tests
def test_student_order_tests():
    (student_test_mod,) = import_student_modules("test_order")
    test_funcs = [
        name for name, obj in vars(student_test_mod).items()
        if name.startswith("test_") and callable(obj)
    ]
    assert len(test_funcs) >= 5, f"test_order.py must contain at least 5 test functions (found {len(test_funcs)})"
