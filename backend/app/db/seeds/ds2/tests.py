import inspect
import io
import runpy
import sys

import pytest
from python_autograder_helpers import import_student_modules

(des_mod,) = import_student_modules("dessert")
DessertItem = getattr(des_mod, "DessertItem", None)
Candy = getattr(des_mod, "Candy", None)
Cookie = getattr(des_mod, "Cookie", None)
IceCream = getattr(des_mod, "IceCream", None)
Sundae = getattr(des_mod, "Sundae", None)
Order = getattr(des_mod, "Order", None)


@pytest.mark.ag_ds1_regression
def test_ds1_regression():
    assert inspect.isclass(DessertItem), "DessertItem must be a class"
    assert inspect.isclass(Candy), "Candy must be a class"
    assert inspect.isclass(Cookie), "Cookie must be a class"
    assert inspect.isclass(IceCream), "IceCream must be a class"
    assert inspect.isclass(Sundae), "Sundae must be a class"

    assert issubclass(Candy, DessertItem), "Candy must inherit from DessertItem"
    assert issubclass(Cookie, DessertItem), "Cookie must inherit from DessertItem"
    assert issubclass(IceCream, DessertItem), "IceCream must inherit from DessertItem"
    assert issubclass(Sundae, IceCream), "Sundae must inherit from IceCream"

    item = DessertItem()
    assert item.name == ""
    item.name = "Cake"
    assert item.name == "Cake"

    candy = Candy()
    assert (candy.name, candy.candy_weight, candy.price_per_pound) == ("", 0.0, 0.0)
    candy.candy_weight = 2.0
    candy.price_per_pound = 4.99
    assert (candy.candy_weight, candy.price_per_pound) == (2.0, 4.99)

    cookie = Cookie()
    assert (cookie.name, cookie.cookie_quantity, cookie.price_per_dozen) == ("", 0, 0.0)
    cookie.cookie_quantity = 24
    cookie.price_per_dozen = 9.99
    assert (cookie.cookie_quantity, cookie.price_per_dozen) == (24, 9.99)

    ic = IceCream()
    assert (ic.name, ic.scoop_count, ic.price_per_scoop) == ("", 0, 0.0)
    ic.scoop_count = 3
    ic.price_per_scoop = 3.0
    assert (ic.scoop_count, ic.price_per_scoop) == (3, 3.0)

    sundae = Sundae()
    assert (
        sundae.name,
        sundae.scoop_count,
        sundae.price_per_scoop,
        sundae.topping_name,
        sundae.topping_price,
    ) == ("", 0, 0.0, "", 0.0)
    sundae.topping_name = "Caramel"
    sundae.topping_price = 1.25
    assert (sundae.topping_name, sundae.topping_price) == ("Caramel", 1.25)


@pytest.mark.ag_order_class
def test_order_class():
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


@pytest.mark.ag_main_output
def test_main_output():
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf
    try:
        runpy.run_path("dessertshop.py", run_name="__main__")
    except Exception as exc:
        raise AssertionError(f"dessertshop.py execution failed: {exc}") from exc
    finally:
        sys.stdout = old_stdout

    lines = [line.strip() for line in stdout_buf.getvalue().strip().splitlines() if line.strip()]
    assert len(lines) >= 7, f"Expected output to contain at least 7 lines, got {len(lines)}"
    expected_names = ["candy corn", "gummy bears", "chocolate chip", "pistachio", "vanilla", "oatmeal"]
    for name in expected_names:
        assert any(name in line.lower() for line in lines), f"Output is missing expected item: {name}"
    assert any("6" in line for line in lines), "Output is missing expected total count of 6 items"
