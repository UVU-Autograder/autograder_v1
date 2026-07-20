from dessert import IceCream


def test_icecream():
    ic = IceCream("Vanilla", 2, 1.5)
    assert ic.name == "Vanilla"
    assert ic.scoop_count == 2
    assert ic.price_per_scoop == 1.5
    assert ic.packaging == "Bowl"
