"""Module 3 Lab 1: Count Occurrences of a Character in a String."""


def count_characters(text: str, char: str) -> int:
    """Count how many times char appears in text using str.count()."""
    return text.count(char)


def main() -> None:
    # Prompt user for string and target character
    user_string = input("Enter a string: ")
    search_char = input("Enter a character to count: ")

    # Store returned value in variable
    char_count = count_characters(user_string, search_char)

    # Print formatted output
    print(f"The character '{search_char}' appears {char_count} time(s) in \"{user_string}\".")


if __name__ == "__main__":
    main()
