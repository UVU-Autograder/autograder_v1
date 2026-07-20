import pytest
from ds_test_helpers import (
    safe_import_dessert,
    import_student_modules,
)


@pytest.mark.ag_ds9_regression
def test_ds9_regression():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    c1 = Candy("Cheap Candy", 1.0, 2.0)
    c2 = Candy("Expensive Candy", 2.0, 2.0)
    assert c1 < c2


@pytest.mark.ag_combinable_protocol
def test_combinable_protocol():
    (cmb_mod,) = import_student_modules("combine")
    Combinable = getattr(cmb_mod, "Combinable", None)
    assert Combinable is not None, "Combinable Protocol missing in combine.py"
    assert hasattr(Combinable, "can_combine"), "Combinable missing can_combine"
    assert hasattr(Combinable, "combine"), "Combinable missing combine"


@pytest.mark.ag_candy_combinable
def test_candy_combinable():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    c1 = Candy("Fudge", 1.0, 2.0)
    c2 = Candy("Fudge", 2.0, 2.0)
    c3 = Candy("Toffee", 1.0, 2.0)

    assert c1.can_combine(c2)
    assert not c1.can_combine(c3)

    c1.combine(c2)
    assert c1.candy_weight == 3.0


@pytest.mark.ag_cookie_combinable
def test_cookie_combinable():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    co1 = Cookie("Choc Chip", 12, 5.0)
    co2 = Cookie("Choc Chip", 6, 5.0)
    co3 = Cookie("Oatmeal", 12, 5.0)

    assert co1.can_combine(co2)
    assert not co1.can_combine(co3)

    co1.combine(co2)
    assert co1.cookie_quantity == 18


@pytest.mark.ag_order_combine
def test_order_combine():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    order = Order()
    c1 = Candy("Fudge", 1.0, 2.0)
    c2 = Candy("Fudge", 2.0, 2.0)
    co1 = Cookie("Choc Chip", 12, 5.0)

    order.add(c1)
    order.add(c2)
    order.add(co1)

    assert len(order) == 2
    assert order.order[0].candy_weight == 3.0
