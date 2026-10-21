"""Module 6 Lab 2: Interleave Odd and Even Integer Lists."""


def interleave(odds: list[int], evens: list[int]) -> list[int]:
    """Interleave values from odds and evens in alternating order without mutating originals."""
    result = []
    max_len = max(len(odds), len(evens))
    for i in range(max_len):
        if i < len(odds):
            result.append(odds[i])
        if i < len(evens):
            result.append(evens[i])
    return result


def main() -> None:
    # Predefined sample lists
    odds = [11, 33, 55]
    evens = [22, 44, 66, 88]

    result = interleave(odds, evens)
    print("Interleaved list:", result)


if __name__ == "__main__":
    main()
