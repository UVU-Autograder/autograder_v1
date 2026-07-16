import pytest
from dessert import DessertItem, Candy, Cookie, IceCream, Sundae

# 1. DessertItem tests
def test_dessert_item_default():
    item = DessertItem()
    assert item.name == ""

def test_dessert_item_parameterized():
    item = DessertItem("Cookie")
    assert item.name == "Cookie"

def test_dessert_item_mutable():
    item = DessertItem("Cookie")
    item.name = "Cake"
    assert item.name == "Cake"


# 2. Candy tests
def test_candy_default():
    candy = Candy()
    assert candy.name == ""
    assert candy.candy_weight == 0.0
    assert candy.price_per_pound == 0.0

def test_candy_parameterized():
    candy = Candy("Gummy Bears", 1.5, 5.99)
    assert candy.name == "Gummy Bears"
    assert candy.candy_weight == 1.5
    assert candy.price_per_pound == 5.99

def test_candy_mutable():
    candy = Candy("Gummy Bears", 1.5, 5.99)
    candy.candy_weight = 2.0
    candy.price_per_pound = 4.99
    assert candy.candy_weight == 2.0
    assert candy.price_per_pound == 4.99


# 3. Cookie tests
def test_cookie_default():
    cookie = Cookie()
    assert cookie.name == ""
    assert cookie.cookie_quantity == 0
    assert cookie.price_per_dozen == 0.0

def test_cookie_parameterized():
    cookie = Cookie("Chocolate Chip", 12, 12.99)
    assert cookie.name == "Chocolate Chip"
    assert cookie.cookie_quantity == 12
    assert cookie.price_per_dozen == 12.99

def test_cookie_mutable():
    cookie = Cookie("Chocolate Chip", 12, 12.99)
    cookie.cookie_quantity = 24
    cookie.price_per_dozen = 9.99
    assert cookie.cookie_quantity == 24
    assert cookie.price_per_dozen == 9.99


# 4. IceCream tests
def test_icecream_default():
    ic = IceCream()
    assert ic.name == ""
    assert ic.scoop_count == 0
    assert ic.price_per_scoop == 0.0

def test_icecream_parameterized():
    ic = IceCream("Vanilla", 2, 2.50)
    assert ic.name == "Vanilla"
    assert ic.scoop_count == 2
    assert ic.price_per_scoop == 2.50

def test_icecream_mutable():
    ic = IceCream("Vanilla", 2, 2.50)
    ic.scoop_count = 3
    ic.price_per_scoop = 3.00
    assert ic.scoop_count == 3
    assert ic.price_per_scoop == 3.00


# 5. Sundae tests
def test_sundae_default():
    sundae = Sundae()
    assert sundae.name == ""
    assert sundae.scoop_count == 0
    assert sundae.price_per_scoop == 0.0
    assert sundae.topping_name == ""
    assert sundae.topping_price == 0.0

def test_sundae_parameterized():
    sundae = Sundae("Fudge Sundae", 2, 3.50, "Hot Fudge", 0.99)
    assert sundae.name == "Fudge Sundae"
    assert sundae.scoop_count == 2
    assert sundae.price_per_scoop == 3.50
    assert sundae.topping_name == "Hot Fudge"
    assert sundae.topping_price == 0.99

def test_sundae_mutable():
    sundae = Sundae("Fudge Sundae", 2, 3.50, "Hot Fudge", 0.99)
    sundae.topping_name = "Caramel"
    sundae.topping_price = 1.25
    assert sundae.topping_name == "Caramel"
    assert sundae.topping_price == 1.25
