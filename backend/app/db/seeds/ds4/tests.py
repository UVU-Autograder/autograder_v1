import pytest
import inspect
import abc

# Import student classes
try:
    from dessert import DessertItem, Candy, Cookie, IceCream, Sundae, Order
except ImportError as exc:
    raise AssertionError(f"Could not import classes from dessert.py: {exc}")


@pytest.mark.ag_abstract_class
def test_abstract_class():
    # 1. DessertItem must be an ABC
    assert issubclass(DessertItem, abc.ABC), "DessertItem must inherit from abc.ABC"
    
    # 2. Cannot instantiate DessertItem directly
    with pytest.raises(TypeError):
        DessertItem("Generic Item")

    # 3. calculate_cost must be abstract
    assert "calculate_cost" in DessertItem.__abstractmethods__, "calculate_cost must be an abstract method"


@pytest.mark.ag_tax_percent
def test_tax_percent():
    # 1. Instances should have tax_percent defaulting to 7.25
    candy = Candy("Test Candy", 1.0, 1.0)
    assert hasattr(candy, "tax_percent"), "DessertItem must have a tax_percent attribute"
    assert candy.tax_percent == 7.25, "Default tax_percent must be 7.25"

    # 2. Modifying tax_percent should change calculate_tax output
    candy.tax_percent = 10.0
    # Cost is 1.0 * 1.0 = 1.0. Tax at 10.0% is 0.10.
    assert candy.calculate_tax() == pytest.approx(0.10), "Modifying tax_percent must update the tax calculation"


@pytest.mark.ag_calculate_cost
def test_calculate_cost():
    # Candy cost = weight * price_per_pound
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_cost() == pytest.approx(0.38), f"Expected 0.38, got {candy.calculate_cost()}"

    # Cookie cost = (quantity / 12) * price_per_dozen
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    assert cookie.calculate_cost() == pytest.approx(2.00), f"Expected 2.00, got {cookie.calculate_cost()}"

    # IceCream cost = scoop_count * price_per_scoop
    ic = IceCream("Pistachio", 2, 0.79)
    assert ic.calculate_cost() == pytest.approx(1.58), f"Expected 1.58, got {ic.calculate_cost()}"

    # Sundae cost = scoops * price_per_scoop + topping_price
    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    assert sundae.calculate_cost() == pytest.approx(3.36), f"Expected 3.36, got {sundae.calculate_cost()}"


@pytest.mark.ag_calculate_tax
def test_calculate_tax():
    # Candy cost = 0.38, tax = 0.38 * 0.0725 = 0.02755 -> 0.03
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_tax() == pytest.approx(0.03), f"Expected 0.03, got {candy.calculate_tax()}"

    # Cookie cost = 2.00, tax = 2.00 * 0.0725 = 0.145 -> 0.14 (due to banker's rounding)
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    assert cookie.calculate_tax() == pytest.approx(0.14), f"Expected 0.14, got {cookie.calculate_tax()}"

    # IceCream cost = 1.58, tax = 1.58 * 0.0725 = 0.11455 -> 0.11
    ic = IceCream("Pistachio", 2, 0.79)
    assert ic.calculate_tax() == pytest.approx(0.11), f"Expected 0.11, got {ic.calculate_tax()}"


@pytest.mark.ag_order_totals
def test_order_totals():
    order = Order()
    order.add(Candy("Candy Corn", 1.5, 0.25))          # Cost: 0.38, Tax: 0.03
    order.add(Candy("Gummy Bears", 0.25, 0.35))        # Cost: 0.09, Tax: 0.01
    order.add(Cookie("Chocolate Chip", 6, 3.99))       # Cost: 2.00, Tax: 0.14
    order.add(IceCream("Pistachio", 2, 0.79))          # Cost: 1.58, Tax: 0.11
    order.add(Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)) # Cost: 3.36, Tax: 0.24
    order.add(Cookie("Oatmeal Raisin", 2, 3.45))       # Cost: 0.57, Tax: 0.04

    # Total Cost = 0.38 + 0.09 + 2.00 + 1.58 + 3.36 + 0.57 = 7.98
    # Total Tax = 0.03 + 0.01 + 0.14 + 0.11 + 0.24 + 0.04 = 0.57
    assert order.order_cost() == pytest.approx(7.98), f"Expected order cost 7.98, got {order.order_cost()}"
    assert order.order_tax() == pytest.approx(0.57), f"Expected order tax 0.57, got {order.order_tax()}"
