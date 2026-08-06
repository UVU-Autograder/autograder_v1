from dessert import Candy, Order


def test_order():
    order = Order()
    assert len(order) == 0
    order.add(Candy("Fudge", 1.0, 2.0))
    assert len(order) == 1
