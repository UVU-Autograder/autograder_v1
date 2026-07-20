import pytest
from dessert import Order, Candy, Cookie
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


def test_order_combine_candy():
    order = Order()
    c1 = Candy("Fudge", 1.0, 2.0)
    c2 = Candy("Fudge", 2.0, 2.0)
    order.add(c1)
    order.add(c2)
    assert len(order) == 1
    assert order.order[0].candy_weight == 3.0
