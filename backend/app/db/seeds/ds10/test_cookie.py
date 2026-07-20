from dessert import Cookie


def test_cookie():
    c = Cookie("Chocolate Chip", 12, 6.0)
    assert c.name == "Chocolate Chip"
    assert c.cookie_quantity == 12
    assert c.price_per_dozen == 6.0
    assert c.packaging == "Box"
