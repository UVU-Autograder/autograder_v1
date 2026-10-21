"""Module 7 Lab 2: Count Vowels in randomText.txt."""


def count_vowels(filename: str = "randomText.txt") -> dict[str, int]:
    """Read a text file and return counts of vowels a, e, i, o, u, y (case-insensitive)."""
    counts = {"a": 0, "e": 0, "i": 0, "o": 0, "u": 0, "y": 0}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                for char in line.lower():
                    if char in counts:
                        counts[char] += 1
    except FileNotFoundError:
        print(f"Error: File '{filename}' was not found.")
        return counts

    return counts


def main() -> None:
    counts = count_vowels("randomText.txt")
    print(
        f"There were {counts['a']} a's, {counts['e']} e's, {counts['i']} i's, "
        f"{counts['o']} o's, {counts['u']} u's, and {counts['y']} y's."
    )


if __name__ == "__main__":
    main()
