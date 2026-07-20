from dessert import Sundae


def test_sundae():
    s = Sundae("Hot Fudge Sundae", 2, 2.0, "Hot Fudge", 1.0)
    assert s.name == "Hot Fudge Sundae"
    assert s.scoop_count == 2
    assert s.price_per_scoop == 2.0
    assert s.topping_name == "Hot Fudge"
    assert s.topping_price == 1.0
    assert s.packaging == "Boat"
