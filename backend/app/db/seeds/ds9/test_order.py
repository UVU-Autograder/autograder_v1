import pytest
from dessert import Candy, Cookie, Order


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


def test_order_sort():
    order = Order()
    c1 = Candy("Cheap", 1.0, 1.0)  # cost 1.0
    c2 = Cookie("Expensive", 12, 12.0)  # cost 12.0
    order.add(c2)
    order.add(c1)
    order.sort()
    assert order.order[0] == c1
    assert order.order[1] == c2
