import abc
import builtins
import importlib
import inspect
import io
import os
import runpy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


_MISSING_MODULE = object()


def import_student_modules(*module_names: str):
    """Import local student modules while temporarily shadowing name collisions."""
    saved_modules = {
        name: sys.modules.get(name, _MISSING_MODULE) for name in module_names
    }
    original_path = list(sys.path)
    try:
        target_dir = os.getenv("STUDENT_SUBMISSION_DIR") or str(Path.cwd())
        sys.path.insert(0, target_dir)
        importlib.invalidate_caches()
        for name in module_names:
            sys.modules.pop(name, None)
        imported = []
        for name in module_names:
            try:
                mod = importlib.import_module(name)
                imported.append(mod)
            except ModuleNotFoundError:
                imported.append(None)
        return tuple(imported)
    finally:
        sys.path[:] = original_path
        for name, module in saved_modules.items():
            if name == "packaging" and "packaging" in sys.modules and hasattr(sys.modules["packaging"], "Packaging"):
                continue
            if module is _MISSING_MODULE:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


class ImportTimeExit(BaseException):
    """Abort student module import when code calls input() at import time."""


def _with_input_blocked(import_fn: Callable[[], Any]) -> Any:
    """Run import_fn with builtins.input raising ImportTimeExit; restore afterward."""
    orig_input = builtins.input

    def mock_input(*args: Any, **kwargs: Any) -> None:
        raise ImportTimeExit()

    builtins.input = mock_input
    try:
        return import_fn()
    finally:
        builtins.input = orig_input


def sequential_input_mock(responses: list[str]):
    it = iter(responses)

    def _mock(prompt: str = "") -> str:
        try:
            return next(it)
        except StopIteration:
            pytest.fail(
                f"Student prompt method called input() more times than expected. "
                f"Responses defined: {responses}"
            )

    return _mock


def safe_import_dessert():
    def _import():
        modules = import_student_modules("packaging", "payment", "combine", "dessert")
        des_mod = modules[3]
        if des_mod is None:
            raise ImportError("Could not find dessert.py")
        return (
            getattr(des_mod, "DessertItem"),
            getattr(des_mod, "Candy"),
            getattr(des_mod, "Cookie"),
            getattr(des_mod, "IceCream"),
            getattr(des_mod, "Sundae"),
            getattr(des_mod, "Order"),
        )

    try:
        return _with_input_blocked(_import)
    except ImportError as exc:
        raise AssertionError(f"Could not import classes from dessert.py: {exc}") from exc
    except ImportTimeExit:
        if "dessert" not in sys.modules:
            raise AssertionError("Could not import dessert.py due to import-time hang")
        mod = sys.modules["dessert"]
        classes = (
            getattr(mod, "DessertItem", None),
            getattr(mod, "Candy", None),
            getattr(mod, "Cookie", None),
            getattr(mod, "IceCream", None),
            getattr(mod, "Sundae", None),
            getattr(mod, "Order", None),
        )
        if any(cls is None for cls in classes):
            raise AssertionError(
                "dessert.py started importing but is missing required classes "
                "(DessertItem, Candy, Cookie, IceCream, Sundae, Order)"
            )
        return classes


def safe_import_dessertshop():
    """Import DessertShop; capture module if student code calls input() mid-import."""
    captured_mod = None
    orig_input = builtins.input

    def mock_input(*args: Any, **kwargs: Any) -> None:
        nonlocal captured_mod
        if "dessertshop" in sys.modules:
            captured_mod = sys.modules["dessertshop"]
        raise ImportTimeExit()

    builtins.input = mock_input
    mod = None
    try:
        mods = import_student_modules("packaging", "payment", "combine", "dessert", "dessertshop")
        mod = mods[4]
    except ImportError as exc:
        raise AssertionError(f"Could not import dessertshop.py: {exc}") from exc
    except ImportTimeExit:
        mod = captured_mod or sys.modules.get("dessertshop")
    finally:
        builtins.input = orig_input

    if mod is None or not hasattr(mod, "DessertShop"):
        raise AssertionError("Could not import DessertShop class from dessertshop.py")
    return mod.DessertShop


def assert_dessertshop_main_output(
    path: str = "dessertshop.py",
    *,
    expected_names: list[str] | None = None,
    min_lines: int = 7,
) -> None:
    names = expected_names or [
        "candy corn",
        "gummy bears",
        "chocolate chip",
        "pistachio",
        "vanilla",
        "oatmeal",
    ]
    stdout_buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = stdout_buf
    try:
        runpy.run_path(path, run_name="__main__")
    except Exception as exc:
        raise AssertionError(f"{path} execution failed: {exc}") from exc
    finally:
        sys.stdout = old_stdout

    lines = [line.strip() for line in stdout_buf.getvalue().strip().splitlines() if line.strip()]
    assert len(lines) >= min_lines, (
        f"Expected output to contain at least {min_lines} lines "
        f"(6 items + 1 count), got {len(lines)}"
    )
    for name in names:
        assert any(name in line.lower() for line in lines), f"Output is missing expected item: {name}"
    assert any("6" in line for line in lines), "Output is missing expected total count of 6 items"


def assert_ds1_hierarchy(DessertItem, Candy, Cookie, IceCream, Sundae):
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


def assert_ds4_abstract_class(DessertItem):
    assert issubclass(DessertItem, abc.ABC), "DessertItem must inherit from abc.ABC"

    with pytest.raises(TypeError):
        DessertItem("Generic Item")

    assert "calculate_cost" in DessertItem.__abstractmethods__, "calculate_cost must be an abstract method"


def assert_ds4_tax_percent(Candy):
    candy = Candy("Test Candy", 1.0, 1.0)
    assert hasattr(candy, "tax_percent"), "DessertItem must have a tax_percent attribute"
    assert candy.tax_percent == 7.25, "Default tax_percent must be 7.25"

    candy.tax_percent = 10.0
    assert candy.calculate_tax() == pytest.approx(0.10), "Modifying tax_percent must update the tax calculation"


def assert_ds4_calculate_cost(Candy, Cookie, IceCream, Sundae):
    candy = Candy("Candy Corn", 1.5, 0.25)
    assert candy.calculate_cost() == pytest.approx(0.38)

    cookie = Cookie("Chocolate Chip", 6, 3.99)
    assert cookie.calculate_cost() == pytest.approx(2.00)

    ic = IceCream("Pistachio", 2, 0.79)
    assert ic.calculate_cost() == pytest.approx(1.58)

    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    assert sundae.calculate_cost() == pytest.approx(3.36)


def assert_ds4_calculate_tax(Candy, Cookie, IceCream):
    candy = Candy("Candy Corn", 1.5, 0.25)
    cookie = Cookie("Chocolate Chip", 6, 3.99)
    ic = IceCream("Pistachio", 2, 0.79)

    assert candy.calculate_tax() == pytest.approx(0.03)
    assert cookie.calculate_tax() == pytest.approx(0.14)
    assert ic.calculate_tax() == pytest.approx(0.11)


def assert_ds4_order_totals(Candy, Cookie, IceCream, Sundae, Order):
    order = Order()
    order.add(Candy("Candy Corn", 1.5, 0.25))
    order.add(Candy("Gummy Bears", 0.25, 0.35))
    order.add(Cookie("Chocolate Chip", 6, 3.99))
    order.add(IceCream("Pistachio", 2, 0.79))
    order.add(Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29))
    order.add(Cookie("Oatmeal Raisin", 2, 3.45))

    assert order.order_cost() == pytest.approx(7.98)
    assert order.order_tax() == pytest.approx(0.57)


def assert_ds4_cost_formulas(Candy, Cookie, IceCream, Sundae, Order, DessertItem):
    assert_ds4_abstract_class(DessertItem)
    assert_ds4_tax_percent(Candy)
    assert_ds4_calculate_cost(Candy, Cookie, IceCream, Sundae)
    assert_ds4_calculate_tax(Candy, Cookie, IceCream)
    assert_ds4_order_totals(Candy, Cookie, IceCream, Sundae, Order)


def assert_ds5_dessertshop(DessertShop, Candy, Cookie, IceCream, Sundae, monkeypatch):
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


def assert_ds6_str_methods(Candy, Cookie, IceCream, Sundae, Order):
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

    ic = IceCream("Pistachio", 2, 0.79)
    ic_str = str(ic)
    assert "Pistachio" in ic_str
    assert "2" in ic_str
    assert "0.79" in ic_str
    assert "1.58" in ic_str
    assert "0.11" in ic_str

    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    sundae_str = str(sundae)
    assert "Vanilla" in sundae_str
    assert "3" in sundae_str
    assert "0.69" in sundae_str
    assert "Hot Fudge" in sundae_str
    assert "1.29" in sundae_str
    assert "3.36" in sundae_str
    assert "0.24" in sundae_str


def assert_ds6_to_list(Candy, Cookie, Order):
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

    found_candy = False
    found_cookie = False
    for row in rows:
        row_str = " ".join(str(cell) for cell in row).lower()
        if "candy corn" in row_str:
            found_candy = True
        if "chocolate chip" in row_str:
            found_cookie = True
    assert found_candy, "to_list output missing Candy Corn"
    assert found_cookie, "to_list output missing Chocolate Chip"
