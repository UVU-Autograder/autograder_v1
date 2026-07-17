import pytest
from ds_test_helpers import (
    safe_import_dessert,
    safe_import_dessertshop,
    assert_ds4_cost_formulas,
    assert_ds5_dessertshop,
)

# Import student classes/modules safely using helper to prevent import-time hangs
DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
DessertShop = safe_import_dessertshop()


@pytest.mark.ag_ds4_regression
def test_ds4_regression():
    assert_ds4_cost_formulas(Candy, Cookie, IceCream, Sundae, Order, DessertItem)


@pytest.mark.ag_dessertshop_class
def test_dessertshop_class(monkeypatch):
    assert_ds5_dessertshop(DessertShop, Candy, Cookie, IceCream, Sundae, monkeypatch)
