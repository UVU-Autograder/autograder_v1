import pytest
from dessert import Candy


def test_candy_cost():
    assert Candy("Candy Corn", 1.5, 0.25).calculate_cost() == pytest.approx(0.38)
