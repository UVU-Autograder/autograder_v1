import pytest
from ds_test_helpers import (
    assert_ds5_dessertshop,
    assert_ds6_str_methods,
    assert_ds6_to_list,
    safe_import_dessert,
    safe_import_dessertshop,
)

DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
DessertShop = safe_import_dessertshop()


@pytest.mark.ag_ds5_regression
def test_ds5_regression(monkeypatch):
    assert_ds5_dessertshop(DessertShop, Candy, Cookie, IceCream, Sundae, monkeypatch)


@pytest.mark.ag_str_methods
def test_str_methods():
    assert_ds6_str_methods(Candy, Cookie, IceCream, Sundae, Order)


@pytest.mark.ag_to_list
def test_to_list():
    assert_ds6_to_list(Candy, Cookie, Order)
