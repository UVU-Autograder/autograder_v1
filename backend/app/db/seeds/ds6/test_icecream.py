import pytest
from dessert import IceCream


def test_icecream_cost():
    assert IceCream("Pistachio", 2, 0.79).calculate_cost() == pytest.approx(1.58)
