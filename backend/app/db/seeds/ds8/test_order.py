import pytest
from dessert import Order
from payment import Payable


def test_order_default_pay_type():
    order = Order()
    assert order.get_pay_type() == "CASH"


def test_order_set_valid_pay_type_card():
    order = Order()
    order.set_pay_type("CARD")
    assert order.get_pay_type() == "CARD"


def test_order_set_valid_pay_type_phone():
    order = Order()
    order.set_pay_type("PHONE")
    assert order.get_pay_type() == "PHONE"


def test_order_set_invalid_pay_type_raises_value_error():
    order = Order()
    with pytest.raises(ValueError):
        order.set_pay_type("BITCOIN")  # type: ignore


def test_order_implements_payable():
    order = Order()
    assert isinstance(order, Payable)
