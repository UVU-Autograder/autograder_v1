"""Module 3 PS Lab 1: Character Shifter - Forward and Reverse."""


def shift_character(char: str, shift: int, mode: str) -> str:
    """Shift an alphabetical character forward or backward while preserving case."""
    if len(char) != 1 or not char.isalpha():
        return char

    shift_amount = shift if mode.lower() == "forward" else -shift

    if char.isupper():
        base = ord("A")
        return chr((ord(char) - base + shift_amount) % 26 + base)
    else:
        base = ord("a")
        return chr((ord(char) - base + shift_amount) % 26 + base)


def main() -> None:
    # Collect character, shift value, and direction
    user_char = input("Enter a character: ")
    shift_val = int(input("Enter shift value: "))
    direction = input("Enter direction (forward/backward): ")

    # Call shift_character and display formatted output
    result = shift_character(user_char, shift_val, direction)
    print(f"Shifted character: {result}")


if __name__ == "__main__":
    main()
