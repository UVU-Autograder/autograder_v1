from __future__ import annotations


class Money:
    """Represents currency using integer dollars and cents with overloaded operators."""

    def __init__(self, dollars: int, cents: int) -> None:
        """Initialize dollars and cents and normalize."""
        self.dollars = int(dollars)
        self.cents = int(cents)
        self.normalize()

    def normalize(self) -> None:
        """Carry cents >= 100 over to dollars."""
        if self.cents >= 100:
            self.dollars += self.cents // 100
            self.cents = self.cents % 100

    def __str__(self) -> str:
        """Return formatted string $dollars.cents."""
        return f"${self.dollars}.{self.cents:02d}"

    def __add__(self, other: Money) -> "Money":
        """Add two Money objects."""
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.dollars + other.dollars, self.cents + other.cents)

    def __mul__(self, other: int) -> "Money":
        """Multiply Money by an integer scalar."""
        if not isinstance(other, int):
            return NotImplemented
        total_cents = (self.dollars * 100 + self.cents) * other
        return Money(0, total_cents)

    def __rmul__(self, other: int) -> "Money":
        """Right-multiply integer scalar by Money object."""
        return self.__mul__(other)

    def __eq__(self, other: object) -> bool:
        """Check equality after normalization."""
        if not isinstance(other, Money):
            return False
        return (self.dollars, self.cents) == (other.dollars, other.cents)


def main() -> None:
    """Main testing entrypoint."""
    m1 = Money(3, 50)
    m2 = Money(2, 75)
    print("m1:", m1)
    print("m2:", m2)

    m3 = m1 + m2
    print("m3:", m3)

    m4 = m1 * 2
    m5 = 3 * m2
    print("m4:", m4)
    print("m5:", m5)

    print(m1 == Money(2, 150))
    print(m1 == Money(3, 49))


if __name__ == "__main__":
    main()
