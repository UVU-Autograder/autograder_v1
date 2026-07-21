"""Autograding test suite for Lab 5: Operator Overloading."""

import pytest
from ds_test_helpers import import_student_modules


@pytest.mark.ag_normalize
def test_normalize() -> None:
    """Verify normalize method carries cents >= 100 to dollars."""
    (money_mod,) = import_student_modules("money")
    Money = getattr(money_mod, "Money")

    m = Money(1, 150)
    assert m.dollars == 2
    assert m.cents == 50

    m2 = Money(0, 325)
    assert m2.dollars == 3
    assert m2.cents == 25


@pytest.mark.ag_str
def test_str() -> None:
    """Verify __str__ string formatting $dollars.cents."""
    (money_mod,) = import_student_modules("money")
    Money = getattr(money_mod, "Money")

    m1 = Money(3, 50)
    assert str(m1) == "$3.50"

    m2 = Money(5, 5)
    assert str(m2) == "$5.05"


@pytest.mark.ag_add
def test_add() -> None:
    """Verify __add__ operator overload for Money addition."""
    (money_mod,) = import_student_modules("money")
    Money = getattr(money_mod, "Money")

    m1 = Money(3, 50)
    m2 = Money(2, 75)
    m3 = m1 + m2

    assert isinstance(m3, Money)
    assert m3.dollars == 6
    assert m3.cents == 25


@pytest.mark.ag_mul
def test_mul() -> None:
    """Verify __mul__ and __rmul__ operator overloads for scalar multiplication."""
    (money_mod,) = import_student_modules("money")
    Money = getattr(money_mod, "Money")

    m1 = Money(3, 50)
    m2 = Money(2, 75)

    m4 = m1 * 2
    assert isinstance(m4, Money)
    assert m4.dollars == 7
    assert m4.cents == 0

    m5 = 3 * m2
    assert isinstance(m5, Money)
    assert m5.dollars == 8
    assert m5.cents == 25


@pytest.mark.ag_eq
def test_eq() -> None:
    """Verify __eq__ operator overload comparing normalized dollar and cent values."""
    (money_mod,) = import_student_modules("money")
    Money = getattr(money_mod, "Money")

    m1 = Money(3, 50)
    m2 = Money(2, 150)
    m3 = Money(3, 49)

    assert m1 == m2
    assert m1 != m3
