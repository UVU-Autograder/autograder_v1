import pytest
from ds_test_helpers import (
    assert_ds6_str_methods,
    assert_ds6_to_list,
    safe_import_dessert,
    safe_import_dessertshop,
    import_student_modules,
)


@pytest.mark.ag_ds6_regression
def test_ds6_regression(monkeypatch):
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    DessertShop = safe_import_dessertshop()
    assert_ds6_str_methods(Candy, Cookie, IceCream, Sundae, Order)
    assert_ds6_to_list(Candy, Cookie, Order)


@pytest.mark.ag_packaging_protocol
def test_packaging_protocol():
    (pkg_mod,) = import_student_modules("packaging")
    Packaging = getattr(pkg_mod, "Packaging", None)
    assert Packaging is not None, "Packaging Protocol missing in packaging.py"
    assert hasattr(Packaging, "__annotations__"), "Packaging Protocol missing annotations"
    assert "packaging" in Packaging.__annotations__, "packaging attribute missing on Packaging Protocol"


@pytest.mark.ag_packaging_defaults
def test_packaging_defaults():
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
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
    DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
    c = Candy("Fudge", 1.0, 2.0)
    assert "(Bag)" in str(c)
