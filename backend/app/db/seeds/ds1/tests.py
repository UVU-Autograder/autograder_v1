import inspect

import pytest

# Import student classes
try:
    from dessert import Candy, Cookie, DessertItem, IceCream, Sundae
except ImportError as exc:
    raise AssertionError(f"Could not import classes from dessert.py: {exc}")


@pytest.mark.ag_dessert_item
def test_dessert_item_class():
    # 1. Existence and properties
    assert inspect.isclass(DessertItem), "DessertItem must be a class"

    # 2. Constructor defaults
    item = DessertItem()
    assert hasattr(item, "name"), "DessertItem must have a 'name' attribute"
    assert item.name == "", "Default name must be empty string"

    # 3. Parameterized constructor
    item2 = DessertItem("Cookie")
    assert item2.name == "Cookie", "Parameterized constructor did not set name correctly"

    # 4. Mutability
    item2.name = "Cake"
    assert item2.name == "Cake", "name attribute must be mutable"


@pytest.mark.ag_candy
def test_candy_class():
    # 1. Inheritance and type
    assert inspect.isclass(Candy), "Candy must be a class"
    assert issubclass(Candy, DessertItem), "Candy must inherit from DessertItem"

    # 2. Constructor defaults
    candy = Candy()
    assert candy.name == "", "Default Candy name must be empty string"
    assert candy.candy_weight == 0.0, "Default candy_weight must be 0.0"
    assert candy.price_per_pound == 0.0, "Default price_per_pound must be 0.0"

    # 3. Parameterized constructor
    candy2 = Candy("Gummy Bears", 1.5, 5.99)
    assert candy2.name == "Gummy Bears", "Candy name not set correctly"
    assert candy2.candy_weight == 1.5, "candy_weight not set correctly"
    assert candy2.price_per_pound == 5.99, "price_per_pound not set correctly"

    # 4. Mutability
    candy2.candy_weight = 2.0
    candy2.price_per_pound = 4.99
    assert candy2.candy_weight == 2.0, "candy_weight must be mutable"
    assert candy2.price_per_pound == 4.99, "price_per_pound must be mutable"


@pytest.mark.ag_cookie
def test_cookie_class():
    # 1. Inheritance and type
    assert inspect.isclass(Cookie), "Cookie must be a class"
    assert issubclass(Cookie, DessertItem), "Cookie must inherit from DessertItem"

    # 2. Constructor defaults
    cookie = Cookie()
    assert cookie.name == "", "Default Cookie name must be empty string"
    assert cookie.cookie_quantity == 0, "Default cookie_quantity must be 0"
    assert cookie.price_per_dozen == 0.0, "Default price_per_dozen must be 0.0"

    # 3. Parameterized constructor
    cookie2 = Cookie("Chocolate Chip", 12, 12.99)
    assert cookie2.name == "Chocolate Chip", "Cookie name not set correctly"
    assert cookie2.cookie_quantity == 12, "cookie_quantity not set correctly"
    assert cookie2.price_per_dozen == 12.99, "price_per_dozen not set correctly"

    # 4. Mutability
    cookie2.cookie_quantity = 24
    cookie2.price_per_dozen = 9.99
    assert cookie2.cookie_quantity == 24, "cookie_quantity must be mutable"
    assert cookie2.price_per_dozen == 9.99, "price_per_dozen must be mutable"


@pytest.mark.ag_icecream
def test_icecream_class():
    # 1. Inheritance and type
    assert inspect.isclass(IceCream), "IceCream must be a class"
    assert issubclass(IceCream, DessertItem), "IceCream must inherit from DessertItem"

    # 2. Constructor defaults
    ic = IceCream()
    assert ic.name == "", "Default IceCream name must be empty string"
    assert ic.scoop_count == 0, "Default scoop_count must be 0"
    assert ic.price_per_scoop == 0.0, "Default price_per_scoop must be 0.0"

    # 3. Parameterized constructor
    ic2 = IceCream("Vanilla", 2, 2.50)
    assert ic2.name == "Vanilla", "IceCream name not set correctly"
    assert ic2.scoop_count == 2, "scoop_count not set correctly"
    assert ic2.price_per_scoop == 2.50, "price_per_scoop not set correctly"

    # 4. Mutability
    ic2.scoop_count = 3
    ic2.price_per_scoop = 3.00
    assert ic2.scoop_count == 3, "scoop_count must be mutable"
    assert ic2.price_per_scoop == 3.00, "price_per_scoop must be mutable"


@pytest.mark.ag_sundae
def test_sundae_class():
    # 1. Inheritance and type
    assert inspect.isclass(Sundae), "Sundae must be a class"
    assert issubclass(Sundae, IceCream), "Sundae must inherit from IceCream"
    assert not issubclass(Sundae, Candy), "Sundae must not inherit from Candy"

    # 2. Constructor defaults
    sundae = Sundae()
    assert sundae.name == "", "Default Sundae name must be empty string"
    assert sundae.scoop_count == 0, "Default Sundae scoop_count must be 0"
    assert sundae.price_per_scoop == 0.0, "Default Sundae price_per_scoop must be 0.0"
    assert sundae.topping_name == "", "Default topping_name must be empty string"
    assert sundae.topping_price == 0.0, "Default topping_price must be 0.0"

    # 3. Parameterized constructor (passing down to IceCream and DessertItem)
    sundae2 = Sundae("Fudge Sundae", 2, 3.50, "Hot Fudge", 0.99)
    assert sundae2.name == "Fudge Sundae", "Sundae name not set correctly"
    assert sundae2.scoop_count == 2, "scoop_count not set correctly"
    assert sundae2.price_per_scoop == 3.50, "price_per_scoop not set correctly"
    assert sundae2.topping_name == "Hot Fudge", "topping_name not set correctly"
    assert sundae2.topping_price == 0.99, "topping_price not set correctly"

    # 4. Mutability
    sundae2.topping_name = "Caramel"
    sundae2.topping_price = 1.25
    assert sundae2.topping_name == "Caramel", "topping_name must be mutable"
    assert sundae2.topping_price == 1.25, "topping_price must be mutable"
