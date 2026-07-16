import pytest
import inspect
import abc
import builtins

# Import student classes safely with input mocked to prevent main() hangs on import
orig_input = builtins.input

class ImportTimeExit(BaseException):
    pass

captured_module = None

def mock_input(*args, **kwargs):
    global captured_module
    import sys
    if "dessertshop" in sys.modules:
        captured_module = sys.modules["dessertshop"]
    raise ImportTimeExit()

builtins.input = mock_input

try:
    from dessert import DessertItem, Candy, Cookie, IceCream, Sundae, Order
except ImportError as exc:
    builtins.input = orig_input
    raise AssertionError(f"Could not import classes from dessert.py: {exc}")

try:
    import dessertshop
except ImportError as exc:
    builtins.input = orig_input
    raise AssertionError(f"Could not import dessertshop.py: {exc}")
except ImportTimeExit:
    pass
finally:
    builtins.input = orig_input

# Retrieve DessertShop class from partially-loaded or fully-loaded module
import sys
if captured_module is not None:
    DessertShopModule = captured_module
elif "dessertshop" in sys.modules:
    DessertShopModule = sys.modules["dessertshop"]
else:
    DessertShopModule = None

if DessertShopModule is None or not hasattr(DessertShopModule, "DessertShop"):
    raise AssertionError("Could not import DessertShop class from dessertshop.py")

DessertShop = DessertShopModule.DessertShop


@pytest.mark.ag_ds4_regression
def test_ds4_regression():
    # 1. DessertItem must be an ABC
    assert issubclass(DessertItem, abc.ABC), "DessertItem must inherit from abc.ABC"
    
    # 2. calculate_cost must be abstract
    assert "calculate_cost" in DessertItem.__abstractmethods__, "calculate_cost must be abstract"

    # 3. Formulas checking
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_cost() == pytest.approx(0.38)
    assert candy.calculate_tax() == pytest.approx(0.03)

    cookie = Cookie("Chocolate Chip", 6, 3.99)
    assert cookie.calculate_cost() == pytest.approx(2.00)
    assert cookie.calculate_tax() == pytest.approx(0.14)


@pytest.mark.ag_dessertshop_class
def test_dessertshop_class(monkeypatch):
    # 1. Verification of class existence and methods
    assert inspect.isclass(DessertShop), "DessertShop must be a class"
    shop = DessertShop()
    
    prompt_methods = [
        "user_prompt_candy",
        "user_prompt_cookie",
        "user_prompt_icecream",
        "user_prompt_sundae"
    ]
    for method in prompt_methods:
        assert hasattr(shop, method), f"DessertShop is missing method: {method}"
        assert inspect.ismethod(getattr(shop, method)), f"{method} must be a method"

    def make_input_mock(responses):
        it = iter(responses)
        def _mock(prompt=""):
            try:
                return next(it)
            except StopIteration:
                pytest.fail(f"Student prompt method called input() more times than expected. Responses defined: {responses}")
        return _mock

    # 2. Test user_prompt_candy (mocking success input)
    monkeypatch.setattr(builtins, "input", make_input_mock(["Gummy Bears", "0.25", "0.35"]))
    candy = shop.user_prompt_candy()
    assert isinstance(candy, Candy), "user_prompt_candy must return a Candy object"
    assert candy.name == "Gummy Bears"
    assert candy.candy_weight == 0.25
    assert candy.price_per_pound == 0.35

    # 4. Test user_prompt_candy (validation loop on negative weight)
    # The first weight input is -0.5 (invalid). The second weight input is 0.25 (valid).
    monkeypatch.setattr(builtins, "input", make_input_mock(["Sour Worms", "-0.5", "0.25", "0.45"]))
    candy2 = shop.user_prompt_candy()
    assert candy2.name == "Sour Worms"
    assert candy2.candy_weight == 0.25
    assert candy2.price_per_pound == 0.45

    # 5. Test user_prompt_cookie (mocking success input)
    monkeypatch.setattr(builtins, "input", make_input_mock(["Chocolate Chip", "12", "3.50"]))
    cookie = shop.user_prompt_cookie()
    assert isinstance(cookie, Cookie), "user_prompt_cookie must return a Cookie object"
    assert cookie.name == "Chocolate Chip"
    assert cookie.cookie_quantity == 12
    assert cookie.price_per_dozen == 3.50

    # 6. Test user_prompt_icecream (mocking success input)
    monkeypatch.setattr(builtins, "input", make_input_mock(["Mint Chip", "3", "1.25"]))
    ic = shop.user_prompt_icecream()
    assert isinstance(ic, IceCream), "user_prompt_icecream must return an IceCream object"
    assert ic.name == "Mint Chip"
    assert ic.scoop_count == 3
    assert ic.price_per_scoop == 1.25

    # 7. Test user_prompt_sundae (mocking success input)
    monkeypatch.setattr(builtins, "input", make_input_mock(["Vanilla", "2", "0.85", "Caramel", "0.99"]))
    sundae = shop.user_prompt_sundae()
    assert isinstance(sundae, Sundae), "user_prompt_sundae must return a Sundae object"
    assert sundae.name == "Vanilla"
    assert sundae.scoop_count == 2
    assert sundae.price_per_scoop == 0.85
    assert sundae.topping_name == "Caramel"
    assert sundae.topping_price == 0.99
