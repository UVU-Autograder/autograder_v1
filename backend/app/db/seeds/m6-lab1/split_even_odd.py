"""Module 6 Lab 1: Split a List into Even and Odd Numbers."""


def split_even_odd(numbers: list[int]) -> tuple[list[int], list[int]]:
    """Separate a list of integers into even and odd lists without mutating the input."""
    # Build new lists for even and odd integers
    evens = [n for n in numbers if n % 2 == 0]
    odds = [n for n in numbers if n % 2 != 0]
    return evens, odds


def main() -> None:
    user_input = input("Enter integers separated by spaces: ").strip()
    if user_input:
        original = [int(x) for x in user_input.split()]
    else:
        original = [1, 2, 3, 4, 5, 6, 7, 8]

    evens, odds = split_even_odd(original)
    print(f"Original list: {original}")
    print(f"Odd values: {odds}")
    print(f"Even values: {evens}")


if __name__ == "__main__":
    main()
