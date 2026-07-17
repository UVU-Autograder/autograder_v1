import pytest
from ds_test_helpers import (
    safe_import_dessert,
    safe_import_dessertshop,
    assert_ds5_dessertshop,
    assert_ds6_str_and_list
)

# Import student classes/modules safely using helper to prevent import-time hangs
DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()
DessertShop = safe_import_dessertshop()


@pytest.mark.ag_ds5_regression
def test_ds5_regression(monkeypatch):
    assert_ds5_dessertshop(DessertShop, Candy, Cookie, IceCream, Sundae, monkeypatch)


@pytest.mark.ag_str_methods
def test_str_methods():
    # Only verify __str__ here, delegation to helper
    # We will pass a stub to assert_ds6_str_and_list
    assert_ds6_str_and_list(Candy, Cookie, IceCream, Sundae, Order, DessertItem)


@pytest.mark.ag_to_list
def test_to_list():
    candy = Candy("Candy Corn", 1.5, 0.25)
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    order = Order()
    order.add(candy)
    order.add(cookie)
    
    rows = order.to_list()
    assert isinstance(rows, list), "to_list must return a list"
    assert len(rows) > 0, "to_list must not be empty"
    # Ensure items are represented in the rows
    found_candy = False
    found_cookie = False
    for row in rows:
        row_str = " ".join(row).lower()
        if "candy corn" in row_str:
            found_candy = True
        if "chocolate chip" in row_str:
            found_cookie = True
    assert found_candy, "to_list output missing Candy Corn"
    assert found_cookie, "to_list output missing Chocolate Chip"
