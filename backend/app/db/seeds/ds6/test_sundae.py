import pytest
from dessert import Sundae


def test_sundae_cost():
    sundae = Sundae("Vanilla", 3, 0.69, "Hot Fudge", 1.29)
    assert sundae.calculate_cost() == pytest.approx(3.36)
