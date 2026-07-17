import pytest
import inspect
import abc
import builtins
import sys

def safe_import_dessert():
    orig_input = builtins.input
    class ImportTimeExit(BaseException):
        pass
        
    def mock_input(*args, **kwargs):
        raise ImportTimeExit()
        
    builtins.input = mock_input
    try:
        from dessert import DessertItem, Candy, Cookie, IceCream, Sundae, Order
        return DessertItem, Candy, Cookie, IceCream, Sundae, Order
    except ImportError as exc:
        raise AssertionError(f"Could not import classes from dessert.py: {exc}")
    except ImportTimeExit:
        if "dessert" in sys.modules:
            mod = sys.modules["dessert"]
            return (
                getattr(mod, "DessertItem", None),
                getattr(mod, "Candy", None),
                getattr(mod, "Cookie", None),
                getattr(mod, "IceCream", None),
                getattr(mod, "Sundae", None),
                getattr(mod, "Order", None),
            )
        raise AssertionError("Could not import dessert.py due to import-time hang")
    finally:
        builtins.input = orig_input


def safe_import_dessertshop():
    orig_input = builtins.input
    class ImportTimeExit(BaseException):
        pass
        
    captured_module = None
    def mock_input(*args, **kwargs):
        nonlocal captured_module
        if "dessertshop" in sys.modules:
            captured_module = sys.modules["dessertshop"]
        raise ImportTimeExit()
        
    builtins.input = mock_input
    try:
        import dessertshop
        mod = dessertshop
    except ImportError as exc:
        raise AssertionError(f"Could not import dessertshop.py: {exc}")
    except ImportTimeExit:
        if captured_module is not None:
            mod = captured_module
        elif "dessertshop" in sys.modules:
            mod = sys.modules["dessertshop"]
        else:
            mod = None
    finally:
        builtins.input = orig_input
        
    if mod is None or not hasattr(mod, "DessertShop"):
        raise AssertionError("Could not import DessertShop class from dessertshop.py")
    return mod.DessertShop


def assert_ds1_hierarchy(DessertItem, Candy, Cookie, IceCream, Sundae):
    # Verify class hierarchy
    assert inspect.isclass(DessertItem), "DessertItem must be a class"
    assert inspect.isclass(Candy), "Candy must be a class"
    assert inspect.isclass(Cookie), "Cookie must be a class"
    assert inspect.isclass(IceCream), "IceCream must be a class"
    assert inspect.isclass(Sundae), "Sundae must be a class"

    assert issubclass(Candy, DessertItem), "Candy must inherit from DessertItem"
    assert issubclass(Cookie, DessertItem), "Cookie must inherit from DessertItem"
    assert issubclass(IceCream, DessertItem), "IceCream must inherit from DessertItem"
    assert issubclass(Sundae, IceCream), "Sundae must inherit from IceCream"

    # Verify attributes and basic constructors
    item = DessertItem("Test Item")
    assert item.name == "Test Item", "DessertItem name not set correctly"

    candy = Candy("Gummy Bears", 1.5, 5.99)
    assert candy.name == "Gummy Bears"
    assert candy.candy_weight == 1.5
    assert candy.price_per_pound == 5.99

    cookie = Cookie("Chocolate Chip", 12, 3.99)
    assert cookie.name == "Chocolate Chip"
    assert cookie.cookie_quantity == 12
    assert cookie.price_per_dozen == 3.99

    ic = IceCream("Vanilla", 2, 1.50)
    assert ic.name == "Vanilla"
    assert ic.scoop_count == 2
    assert ic.price_per_scoop == 1.50

    sundae = Sundae("Chocolate", 2, 1.50, "Hot Fudge", 0.50)
    assert sundae.name == "Chocolate"
    assert sundae.scoop_count == 2
    assert sundae.price_per_scoop == 1.50
    assert sundae.topping_name == "Hot Fudge"
    assert sundae.topping_price == 0.50


def assert_ds2_order(Order, DessertItem):
    assert inspect.isclass(Order), "Order must be a class"
    order = Order()
    assert hasattr(order, "order"), "Order must have an 'order' attribute"
    assert isinstance(order.order, list), "order attribute must be a list"
    assert len(order) == 0, "Initial order length must be 0"

    assert hasattr(order, "add"), "Order must have an add method"
    assert hasattr(order, "__len__"), "Order must support len()"
    assert hasattr(order, "__iter__"), "Order must support iteration"

    item1 = DessertItem("Item 1")
    item2 = DessertItem("Item 2")
    order.add(item1)
    assert len(order) == 1, "Order length must be 1 after adding an item"
    order.add(item2)

    assert len(order) == 2, "Order len() should reflect added items"
    items = list(order)
    assert items == [item1, item2], "Order iteration should return items in order"


def assert_ds4_cost_formulas(Candy, Cookie, IceCream, Sundae, Order, DessertItem):
    # 1. ABC Check
    assert issubclass(DessertItem, abc.ABC), "DessertItem must inherit from abc.ABC"
    
    # Cannot instantiate DessertItem directly
    with pytest.raises(TypeError):
        DessertItem("Generic Item")

    # calculate_cost must be abstract
    assert "calculate_cost" in DessertItem.__abstractmethods__, "calculate_cost must be an abstract method"

    # 2. Tax Percent attribute
    candy = Candy("Test Candy", 1.0, 1.0)
    assert hasattr(candy, "tax_percent"), "DessertItem must have a tax_percent attribute"
    assert candy.tax_percent == 7.25, "Default tax_percent must be 7.25"

    candy.tax_percent = 10.0
    assert candy.calculate_tax() == pytest.approx(0.10), "Modifying tax_percent must update the tax calculation"

    # Restore tax_percent
    candy.tax_percent = 7.25

    # 3. Cost Formulas
    # Candy cost = weight * price_per_pound
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_cost() == pytest.approx(0.38)

    # Cookie cost = (quantity / 12) * price_per_dozen
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    assert cookie.calculate_cost() == pytest.approx(2.00)

    # IceCream cost = scoop_count * price_per_scoop
    ic = IceCream("Pistachio", 2, 0.79)
    assert ic.calculate_cost() == pytest.approx(1.58)

    # Sundae cost = scoops * price_per_scoop + topping_price
    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    assert sundae.calculate_cost() == pytest.approx(3.36)

    # 4. Tax Formulas (Banker's rounding checking)
    assert candy.calculate_tax() == pytest.approx(0.03)
    assert cookie.calculate_tax() == pytest.approx(0.14)
    assert ic.calculate_tax() == pytest.approx(0.11)

    # 5. Order Totals
    order = Order()
    order.add(Candy("Candy Corn", 1.5, 0.25))          # Cost: 0.38, Tax: 0.03
    order.add(Candy("Gummy Bears", 0.25, 0.35))        # Cost: 0.09, Tax: 0.01
    order.add(Cookie("Chocolate Chip", 6, 3.99))       # Cost: 2.00, Tax: 0.14
    order.add(IceCream("Pistachio", 2, 0.79))          # Cost: 1.58, Tax: 0.11
    order.add(Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)) # Cost: 3.36, Tax: 0.24
    order.add(Cookie("Oatmeal Raisin", 2, 3.45))       # Cost: 0.57, Tax: 0.04

    assert order.order_cost() == pytest.approx(7.98)
    assert order.order_tax() == pytest.approx(0.57)


def assert_ds5_dessertshop(DessertShop, Candy, Cookie, IceCream, Sundae, monkeypatch):
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

    # Test user_prompt_candy (mocking success input)
    monkeypatch.setattr("builtins.input", make_input_mock(["Gummy Bears", "0.25", "0.35"]))
    candy = shop.user_prompt_candy()
    assert isinstance(candy, Candy), "user_prompt_candy must return a Candy object"
    assert candy.name == "Gummy Bears"
    assert candy.candy_weight == 0.25
    assert candy.price_per_pound == 0.35

    # Test user_prompt_candy (validation loop on negative weight)
    monkeypatch.setattr("builtins.input", make_input_mock(["Sour Worms", "-0.5", "0.25", "0.45"]))
    candy2 = shop.user_prompt_candy()
    assert candy2.name == "Sour Worms"
    assert candy2.candy_weight == 0.25
    assert candy2.price_per_pound == 0.45

    # Test user_prompt_cookie (mocking success input)
    monkeypatch.setattr("builtins.input", make_input_mock(["Chocolate Chip", "12", "3.50"]))
    cookie = shop.user_prompt_cookie()
    assert isinstance(cookie, Cookie), "user_prompt_cookie must return a Cookie object"
    assert cookie.name == "Chocolate Chip"
    assert cookie.cookie_quantity == 12
    assert cookie.price_per_dozen == 3.50

    # Test user_prompt_icecream (mocking success input)
    monkeypatch.setattr("builtins.input", make_input_mock(["Mint Chip", "3", "1.25"]))
    ic = shop.user_prompt_icecream()
    assert isinstance(ic, IceCream), "user_prompt_icecream must return an IceCream object"
    assert ic.name == "Mint Chip"
    assert ic.scoop_count == 3
    assert ic.price_per_scoop == 1.25

    # Test user_prompt_sundae (mocking success input)
    monkeypatch.setattr("builtins.input", make_input_mock(["Vanilla", "2", "0.85", "Caramel", "0.99"]))
    sundae = shop.user_prompt_sundae()
    assert isinstance(sundae, Sundae), "user_prompt_sundae must return a Sundae object"
    assert sundae.name == "Vanilla"
    assert sundae.scoop_count == 2
    assert sundae.price_per_scoop == 0.85
    assert sundae.topping_name == "Caramel"
    assert sundae.topping_price == 0.99


def assert_ds6_str_and_list(Candy, Cookie, IceCream, Sundae, Order, DessertItem):
    # Verify __str__ overrides
    assert Candy.__str__ is not object.__str__, "Candy must override __str__"
    assert Cookie.__str__ is not object.__str__, "Cookie must override __str__"
    assert IceCream.__str__ is not object.__str__, "IceCream must override __str__"
    assert Sundae.__str__ is not object.__str__, "Sundae must override __str__"
    assert Order.__str__ is not object.__str__, "Order must override __str__"

    # Verify Candy __str__ content
    candy = Candy("Candy Corn", 1.5, 0.25)
    candy_str = str(candy)
    assert "Candy Corn" in candy_str
    assert "1.5" in candy_str
    assert "0.25" in candy_str
    assert "0.38" in candy_str
    assert "0.03" in candy_str

    # Verify Cookie __str__ content
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    cookie_str = str(cookie)
    assert "Chocolate Chip" in cookie_str
    assert "6" in cookie_str
    assert "3.99" in cookie_str
    assert any(x in cookie_str for x in ["2.00", "2.0", "2"])
    assert "0.14" in cookie_str

    # Verify IceCream __str__ content
    ic = IceCream("Pistachio", 2, 0.79)
    ic_str = str(ic)
    assert "Pistachio" in ic_str
    assert "2" in ic_str
    assert "0.79" in ic_str
    assert "1.58" in ic_str
    assert "0.11" in ic_str

    # Verify Sundae __str__ content
    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    sundae_str = str(sundae)
    assert "Vanilla" in sundae_str
    assert "3" in sundae_str
    assert "0.69" in sundae_str
    assert "Hot Fudge" in sundae_str
    assert "1.29" in sundae_str
    assert "3.36" in sundae_str
    assert "0.24" in sundae_str

    # Verify Order.to_list() format
    order = Order()
    order.add(candy)
    order.add(cookie)
    
    rows = order.to_list()
    assert isinstance(rows, list), "to_list must return a list"
    assert len(rows) > 0, "to_list must not be empty"
    for row in rows:
        assert isinstance(row, list), "to_list must return a 2D list (list of lists)"

