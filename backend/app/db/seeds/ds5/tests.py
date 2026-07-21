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


@pytest.mark.ag_ds4_regression
def test_ds4_regression():
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_cost() == pytest.approx(0.38)
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    assert cookie.calculate_cost() == pytest.approx(2.00)
    ic = IceCream("Pistachio", 2, 0.79)
    assert ic.calculate_cost() == pytest.approx(1.58)
    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    assert sundae.calculate_cost() == pytest.approx(3.36)


@pytest.mark.ag_dessertshop_class
def test_dessertshop_class(monkeypatch):
    assert inspect.isclass(DessertShop), "DessertShop must be a class"
    shop = DessertShop()

    prompt_methods = [
        "user_prompt_candy",
        "user_prompt_cookie",
        "user_prompt_icecream",
        "user_prompt_sundae",
    ]
    for method in prompt_methods:
        assert hasattr(shop, method), f"DessertShop is missing method: {method}"
        assert inspect.ismethod(getattr(shop, method)), f"{method} must be a method"

    monkeypatch.setattr("builtins.input", sequential_input_mock(["Gummy Bears", "0.25", "0.35"]))
    candy = shop.user_prompt_candy()
    assert isinstance(candy, Candy), "user_prompt_candy must return a Candy object"
    assert candy.name == "Gummy Bears"
    assert candy.candy_weight == 0.25
    assert candy.price_per_pound == 0.35

    monkeypatch.setattr("builtins.input", sequential_input_mock(["Sour Worms", "-0.5", "0.25", "0.45"]))
    candy2 = shop.user_prompt_candy()
    assert candy2.name == "Sour Worms"
    assert candy2.candy_weight == 0.25
    assert candy2.price_per_pound == 0.45

    monkeypatch.setattr("builtins.input", sequential_input_mock(["Chocolate Chip", "12", "3.50"]))
    cookie = shop.user_prompt_cookie()
    assert isinstance(cookie, Cookie), "user_prompt_cookie must return a Cookie object"
    assert cookie.name == "Chocolate Chip"
    assert cookie.cookie_quantity == 12
    assert cookie.price_per_dozen == 3.50

    monkeypatch.setattr("builtins.input", sequential_input_mock(["Mint Chip", "3", "1.25"]))
    ic = shop.user_prompt_icecream()
    assert isinstance(ic, IceCream), "user_prompt_icecream must return an IceCream object"
    assert ic.name == "Mint Chip"
    assert ic.scoop_count == 3
    assert ic.price_per_scoop == 1.25

    monkeypatch.setattr("builtins.input", sequential_input_mock(["Vanilla", "2", "0.85", "Caramel", "0.99"]))
    sundae = shop.user_prompt_sundae()
    assert isinstance(sundae, Sundae), "user_prompt_sundae must return a Sundae object"
    assert sundae.name == "Vanilla"
    assert sundae.scoop_count == 2
    assert sundae.price_per_scoop == 0.85
    assert sundae.topping_name == "Caramel"
    assert sundae.topping_price == 0.99
