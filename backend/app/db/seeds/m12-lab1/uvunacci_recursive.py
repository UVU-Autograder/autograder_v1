"""Generate UVUnacci Series Using Recursion.

CS 1400 - Module 12 Lab 1
Calculates the UVUnacci sequence where each term is the sum of the preceding three terms:
UVUnacci(0) = 0
UVUnacci(1) = 1
UVUnacci(2) = 2
UVUnacci(n) = UVUnacci(n-1) + UVUnacci(n-2) + UVUnacci(n-3) for n >= 3
"""

from functools import lru_cache


@lru_cache(maxsize=None)
def uvunacci_recursive(n):
    """Return the n-th term of the UVUnacci sequence using recursion."""
    # Base cases
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 2

    # Recursive step: sum of the last three terms
    return (
        uvunacci_recursive(n - 1)
        + uvunacci_recursive(n - 2)
        + uvunacci_recursive(n - 3)
    )


def main():
    # Generate the first 30 terms (terms 0 through 29)
    sequence = [uvunacci_recursive(i) for i in range(30)]

    # Print the resulting sequence
    print("UVUnacci (first 30 terms):")
    print(sequence)


if __name__ == "__main__":
    main()
