import pytest
import inspect
import io
import sys
import runpy

# Import student classes
try:
    from dessert import DessertItem, Candy, Cookie, IceCream, Sundae, Order
except ImportError as exc:
    raise AssertionError(f"Could not import classes from dessert.py: {exc}")


@pytest.mark.ag_ds1_regression
def test_ds1_regression():
    # Verify DessertItem
    assert inspect.isclass(DessertItem), "DessertItem must be a class"
    item = DessertItem("Cookie")
    assert item.name == "Cookie"

    # Verify Candy
    assert inspect.isclass(Candy)
    assert issubclass(Candy, DessertItem)
    candy = Candy("Gummy Bears", 1.5, 5.99)
    assert candy.name == "Gummy Bears"
    assert candy.candy_weight == 1.5
    assert candy.price_per_pound == 5.99

    # Verify Cookie
    assert inspect.isclass(Cookie)
    assert issubclass(Cookie, DessertItem)
    cookie = Cookie("Chocolate Chip", 12, 12.99)
    assert cookie.name == "Chocolate Chip"
    assert cookie.cookie_quantity == 12
    assert cookie.price_per_dozen == 12.99

    # Verify IceCream
    assert inspect.isclass(IceCream)
    assert issubclass(IceCream, DessertItem)
    ic = IceCream("Vanilla", 2, 2.50)
    assert ic.name == "Vanilla"
    assert ic.scoop_count == 2
    assert ic.price_per_scoop == 2.50

    # Verify Sundae
    assert inspect.isclass(Sundae)
    assert issubclass(Sundae, IceCream)
    sundae = Sundae("Fudge Sundae", 2, 3.50, "Hot Fudge", 0.99)
    assert sundae.name == "Fudge Sundae"
    assert sundae.topping_name == "Hot Fudge"
    assert sundae.topping_price == 0.99


@pytest.mark.ag_order_class
def test_order_class():
    # 1. Verification of class and methods
    assert inspect.isclass(Order), "Order must be a class"
    
    order = Order()
    assert hasattr(order, "order"), "Order must have an 'order' attribute"
    assert isinstance(order.order, list), "order attribute must be a list"
    assert len(order) == 0, "Initial order length must be 0"

    # 2. Test add and len
    item1 = DessertItem("Test Item 1")
    item2 = DessertItem("Test Item 2")
    order.add(item1)
    assert len(order) == 1, "Order length must be 1 after adding an item"
    order.add(item2)
    assert len(order) == 2, "Order length must be 2 after adding two items"

    # 3. Test iteration protocol (iter/next)
    iter_obj = iter(order)
    assert iter_obj is order or hasattr(iter_obj, "__next__"), "__iter__ must return an iterator"
    
    first = next(iter_obj)
    assert first is item1, "First item in iteration must be the first item added"
    second = next(iter_obj)
    assert second is item2, "Second item in iteration must be the second item added"
    
    with pytest.raises(StopIteration):
        next(iter_obj)


@pytest.mark.ag_main_output
def test_main_output():
    # Run the main function in dessertshop.py and capture stdout
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf
    try:
        runpy.run_path("dessertshop.py", run_name="__main__")
    except Exception as exc:
        raise AssertionError(f"dessertshop.py execution failed: {exc}")
    finally:
        sys.stdout = old_stdout

    captured = stdout_buf.getvalue()
    lines = [line.strip() for line in captured.strip().splitlines() if line.strip()]

    assert len(lines) >= 7, f"Expected output to contain at least 7 lines (6 items + 1 count), got {len(lines)}"

    # Check for the 6 required names
    names = ["candy corn", "gummy bears", "chocolate chip", "pistachio", "vanilla", "oatmeal"]
    for name in names:
        assert any(name in line.lower() for line in lines), f"Output is missing expected item: {name}"

    # Check for total count "6" in the output
    assert any("6" in line for line in lines), "Output is missing expected total count of 6 items"
