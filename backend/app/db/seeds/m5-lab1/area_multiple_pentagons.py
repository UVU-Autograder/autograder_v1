"""Module 5 Lab 1: Compute Total Area of Multiple Regular Pentagons."""

import math


def areaRegularPentagon(lengthSide: float) -> float:
    """Calculate the area of a single regular pentagon using lengthSide."""
    # Area = (5 * side^2) / (4 * tan(pi / 5))
    return (5 * (lengthSide ** 2)) / (4 * math.tan(math.pi / 5))


def areaMultiplePentagons(numPentagons: int, lengthSide: float) -> float:
    """Calculate the total area for multiple regular pentagons by reusing areaRegularPentagon."""
    return numPentagons * areaRegularPentagon(lengthSide)


def main() -> None:
    total = areaMultiplePentagons(3, 7)
    print(f"Total area for 3 pentagons with side 7: {total:.4f}")


if __name__ == "__main__":
    main()
