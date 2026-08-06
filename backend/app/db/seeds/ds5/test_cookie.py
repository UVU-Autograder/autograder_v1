import pytest
from dessert import Cookie


def test_cookie_cost():
    assert Cookie("Chocolate Chip", 6, 3.99).calculate_cost() == pytest.approx(2.0)
