import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_ds6_regression
def test_ds6_regression(monkeypatch):
    des_mod, shop_mod = import_student_modules("dessert", "dessertshop")
    DessertItem = getattr(des_mod, "DessertItem", None)
    Candy = getattr(des_mod, "Candy", None)
    Cookie = getattr(des_mod, "Cookie", None)
    IceCream = getattr(des_mod, "IceCream", None)
    Sundae = getattr(des_mod, "Sundae", None)
    Order = getattr(des_mod, "Order", None)
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert "Candy Corn" in str(candy)
    order = Order()
    order.add(candy)
    assert len(order.to_list()) > 0


@pytest.mark.ag_packaging_protocol
def test_packaging_protocol():
    (pkg_mod,) = import_student_modules("packaging")
    Packaging = getattr(pkg_mod, "Packaging", None)
    assert Packaging is not None, "Packaging Protocol missing in packaging.py"
    assert hasattr(Packaging, "__annotations__"), "Packaging Protocol missing annotations"
    assert "packaging" in Packaging.__annotations__, "packaging attribute missing on Packaging Protocol"


@pytest.mark.ag_packaging_defaults
def test_packaging_defaults():
    (des_mod,) = import_student_modules("dessert")
    Candy = getattr(des_mod, "Candy")
    Cookie = getattr(des_mod, "Cookie")
    IceCream = getattr(des_mod, "IceCream")
    Sundae = getattr(des_mod, "Sundae")
    c = Candy("Fudge", 1.0, 2.0)
    co = Cookie("Choc Chip", 12, 5.0)
    i = IceCream("Vanilla", 2, 1.5)
    s = Sundae("Banana Split", 3, 2.0, "Hot Fudge", 1.0)
    assert c.packaging == "Bag"
    assert co.packaging == "Box"
    assert i.packaging == "Bowl"
    assert s.packaging == "Boat"


@pytest.mark.ag_packaging_in_str
def test_packaging_in_str():
    (des_mod,) = import_student_modules("dessert")
    Candy = getattr(des_mod, "Candy")
    c = Candy("Fudge", 1.0, 2.0)
    assert "(Bag)" in str(c)
