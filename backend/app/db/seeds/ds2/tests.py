import pytest

from ds_test_helpers import (
    assert_dessertshop_main_output,
    assert_ds1_hierarchy,
    assert_ds2_order,
    safe_import_dessert,
)

DessertItem, Candy, Cookie, IceCream, Sundae, Order = safe_import_dessert()


@pytest.mark.ag_ds1_regression
def test_ds1_regression():
    assert_ds1_hierarchy(DessertItem, Candy, Cookie, IceCream, Sundae)


@pytest.mark.ag_order_class
def test_order_class():
    assert_ds2_order(Order, DessertItem)


@pytest.mark.ag_main_output
def test_main_output():
    assert_dessertshop_main_output()
