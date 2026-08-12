from dessert import Candy


def test_candy():
    c = Candy("Fudge", 2.0, 3.0)
    assert c.name == "Fudge"
    assert c.candy_weight == 2.0
    assert c.price_per_pound == 3.0
    assert c.packaging == "Bag"
