import inspect

from dessert import DessertItem


def test_dessert_item_is_abstract():
    assert inspect.isabstract(DessertItem)
