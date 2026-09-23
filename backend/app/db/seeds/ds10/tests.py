import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_ds9_regression
def test_ds9_regression():
    (des_mod,) = import_student_modules("dessert")
    Candy = des_mod.Candy
    Order = des_mod.Order
    c1 = Candy("Cheap Candy", 1.0, 2.0)
    c2 = Candy("Expensive Candy", 2.0, 2.0)
    assert c1 < c2

    order = Order()
    order.add(c2)
    order.add(c1)
    order.sort()
    assert order.order == [c1, c2], "Order.sort() must sort in ascending order by cost"


@pytest.mark.ag_combinable_protocol
def test_combinable_protocol():
    (cmb_mod,) = import_student_modules("combine")
    Combinable = getattr(cmb_mod, "Combinable", None)
    assert Combinable is not None, "Combinable Protocol missing in combine.py"
    assert hasattr(Combinable, "can_combine"), "Combinable missing can_combine"
    assert hasattr(Combinable, "combine"), "Combinable missing combine"


@pytest.mark.ag_candy_combinable
def test_candy_combinable():
    (des_mod,) = import_student_modules("dessert")
    Candy = des_mod.Candy
    c1 = Candy("Fudge", 1.0, 2.0)
    c2 = Candy("Fudge", 2.0, 2.0)
    c3 = Candy("Toffee", 1.0, 2.0)
    c4 = Candy("Fudge", 1.0, 3.0)  # different price per pound

    assert c1.can_combine(c2)
    assert not c1.can_combine(c3), "Candy cannot combine with different name"
    assert not c1.can_combine(c4), "Candy cannot combine with different price per pound"

    ret = c1.combine(c2)
    assert ret is c1, "Candy.combine must return modified self"
    assert c1.candy_weight == 3.0


@pytest.mark.ag_cookie_combinable
def test_cookie_combinable():
    (des_mod,) = import_student_modules("dessert")
    Cookie = des_mod.Cookie
    co1 = Cookie("Choc Chip", 12, 5.0)
    co2 = Cookie("Choc Chip", 6, 5.0)
    co3 = Cookie("Oatmeal", 12, 5.0)
    co4 = Cookie("Choc Chip", 12, 6.0)  # different price per dozen

    assert co1.can_combine(co2)
    assert not co1.can_combine(co3), "Cookie cannot combine with different name"
    assert not co1.can_combine(co4), "Cookie cannot combine with different price per dozen"

    ret = co1.combine(co2)
    assert ret is co1, "Cookie.combine must return modified self"
    assert co1.cookie_quantity == 18


@pytest.mark.ag_order_combine
def test_order_combine():
    (des_mod,) = import_student_modules("dessert")
    Candy = des_mod.Candy
    Cookie = des_mod.Cookie
    Order = des_mod.Order
    order = Order()
    c1 = Candy("Fudge", 1.0, 2.0)
    c2 = Candy("Fudge", 2.0, 2.0)
    co1 = Cookie("Choc Chip", 12, 5.0)

    order.add(c1)
    order.add(c2)
    order.add(co1)

    assert len(order) == 2
    assert order.order[0].candy_weight == 3.0
