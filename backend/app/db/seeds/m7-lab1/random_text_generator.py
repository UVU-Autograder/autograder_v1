"""Module 7 Lab 1: Random Text File Generator."""

import random
import string


def make_word() -> str:
    """Generate a random word with 5 to 10 lowercase letters."""
    length = random.randint(5, 10)
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def make_line() -> str:
    """Generate a line consisting of 8 to 10 space-separated random words."""
    num_words = random.randint(8, 10)
    words = [make_word() for _ in range(num_words)]
    return " ".join(words)


def write_random_text(filename: str = "randomText.txt", num_lines: int = 100) -> None:
    """Write at least 100 lines of random words to the specified file."""
    # Write generated lines ending with newlines to file
    with open(filename, "w", encoding="utf-8") as f:
        for _ in range(num_lines):
            f.write(make_line() + "\n")


def main() -> None:
    write_random_text()
    print("Generated randomText.txt successfully.")


if __name__ == "__main__":
    main()
