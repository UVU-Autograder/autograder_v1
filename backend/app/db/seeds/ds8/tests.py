import typing

import pytest
from python_autograder_helpers import import_student_modules
from student_test_helpers import assert_student_pytest_passes, assert_test_function_count


@pytest.mark.ag_ds7_regression
def test_ds7_regression():
    (des_mod,) = import_student_modules("dessert")
    Candy = des_mod.Candy
    Cookie = des_mod.Cookie
    IceCream = des_mod.IceCream
    Sundae = des_mod.Sundae
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
    assert typing.Protocol in getattr(Payable, "__mro__", ()) or getattr(Payable, "_is_protocol", False), (
        "Payable must be a typing.Protocol"
    )
    assert hasattr(Payable, "get_pay_type"), "Payable missing get_pay_type"
    assert hasattr(Payable, "set_pay_type"), "Payable missing set_pay_type"

    PayType = getattr(pay_mod, "PayType", None)
    assert PayType is not None, "PayType type missing in payment.py"
    if hasattr(PayType, "__members__"):
        assert all(k in PayType.__members__ for k in ("CASH", "CARD", "PHONE")), "PayType enum must include CASH, CARD, and PHONE"
    elif hasattr(typing, "get_args"):
        args = typing.get_args(PayType)
        if args:
            assert all(k in args for k in ("CASH", "CARD", "PHONE")), "PayType Literal must include 'CASH', 'CARD', and 'PHONE'"


@pytest.mark.ag_order_payable
def test_order_payable():
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


@pytest.mark.ag_student_order_tests
def test_student_order_tests():
    assert_test_function_count("test_order.py", minimum=5)
    assert_student_pytest_passes("test_order.py", minimum=5, timeout_seconds=10)
