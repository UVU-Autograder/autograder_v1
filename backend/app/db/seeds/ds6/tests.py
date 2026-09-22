import inspect

import pytest
from python_autograder_helpers import (
    import_student_modules,
    sequential_input_mock,
)

des_mod, shop_mod = import_student_modules("dessert", "dessertshop")
DessertItem = getattr(des_mod, "DessertItem", None)
Candy = getattr(des_mod, "Candy", None)
Cookie = getattr(des_mod, "Cookie", None)
IceCream = getattr(des_mod, "IceCream", None)
Sundae = getattr(des_mod, "Sundae", None)
Order = getattr(des_mod, "Order", None)
DessertShop = getattr(shop_mod, "DessertShop", None)


@pytest.mark.ag_ds5_regression
def test_ds5_regression(monkeypatch):
    assert inspect.isclass(DessertShop), "DessertShop must be a class"
    shop = DessertShop()
    monkeypatch.setattr("builtins.input", sequential_input_mock(["Gummy Bears", "0.25", "0.35"]))
    candy = shop.user_prompt_candy()
    assert candy.name == "Gummy Bears"


@pytest.mark.ag_str_methods
def test_str_methods():
    assert Candy.__str__ is not object.__str__, "Candy must override __str__"
    assert Cookie.__str__ is not object.__str__, "Cookie must override __str__"
    assert IceCream.__str__ is not object.__str__, "IceCream must override __str__"
    assert Sundae.__str__ is not object.__str__, "Sundae must override __str__"
    assert Order.__str__ is not object.__str__, "Order must override __str__"

    candy = Candy("Candy Corn", 1.5, 0.25)
    candy_str = str(candy)
    assert "Candy Corn" in candy_str
    assert "1.5" in candy_str
    assert "0.25" in candy_str
    assert "0.38" in candy_str
    assert "0.03" in candy_str

    cookie = Cookie("Chocolate Chip", 6, 3.99)
    cookie_str = str(cookie)
    assert "Chocolate Chip" in cookie_str
    assert "6" in cookie_str
    assert "3.99" in cookie_str
    assert any(x in cookie_str for x in ["2.00", "2.0", "2"])
    assert "0.14" in cookie_str


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
    for row in rows:
        assert isinstance(row, list), "to_list must return a 2D list (list of lists)"
