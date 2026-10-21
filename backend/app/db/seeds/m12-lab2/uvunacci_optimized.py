"""Optimize UVUnacci Using Memoization and Iteration.

CS 1400 - Module 12 Lab 2
Demonstrates top-down recursion with manual memoization vs bottom-up iteration
compared against baseline naive recursion.
"""

import time


def uvunacci_recursive(n):
    """Compute n-th UVUnacci term using naive recursion."""
    # Base cases
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 2

    return (
        uvunacci_recursive(n - 1)
        + uvunacci_recursive(n - 2)
        + uvunacci_recursive(n - 3)
    )


def uvunacci_memoized(n, memo_dict=None):
    """Compute n-th UVUnacci term using recursion with manual dictionary memoization."""
    if memo_dict is None:
        memo_dict = {}

    # Check memo dictionary first
    if n in memo_dict:
        return memo_dict[n]

    # Base cases
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 2

    # Recursive step and store in memo
    memo_dict[n] = (
        uvunacci_memoized(n - 1, memo_dict)
        + uvunacci_memoized(n - 2, memo_dict)
        + uvunacci_memoized(n - 3, memo_dict)
    )
    return memo_dict[n]


def uvunacci_iterative(n):
    """Compute n-th UVUnacci term using bottom-up iteration with a loop."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    if n == 2:
        return 2

    a, b, c = 0, 1, 2
    for _ in range(3, n + 1):
        a, b, c = b, c, a + b + c
    return c


def main():
    n = 25
    print(f"Generating UVUnacci({n})...")

    # Measure recursive
    start_rec = time.perf_counter()
    val_rec = uvunacci_recursive(n)
    time_rec = time.perf_counter() - start_rec

    # Measure memoized
    start_memo = time.perf_counter()
    val_memo = uvunacci_memoized(n, {})
    time_memo = time.perf_counter() - start_memo

    # Measure iterative
    start_iter = time.perf_counter()
    val_iter = uvunacci_iterative(n)
    time_iter = time.perf_counter() - start_iter

    # Display timings
    print(f"Recursive:      {val_rec} -> Time: {time_rec:.6f} seconds")
    print(f"Memoized:       {val_memo} -> Time: {time_memo:.6f} seconds")
    print(f"Iterative:      {val_iter} -> Time: {time_iter:.6f} seconds")

    # Summary
    print("\nSummary:")
    print("- Iterative and memoized approaches are significantly faster than naive recursion.")
    print("- Memoization avoids exponential repeated sub-problem calculations.")
    print("- Iteration is most efficient because it avoids recursion call stack overhead.")


if __name__ == "__main__":
    main()
