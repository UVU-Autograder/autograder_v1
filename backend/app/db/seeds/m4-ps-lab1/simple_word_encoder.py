"""Module 4 Problem Solving Lab 1: Word Encoder - Shift All Letters."""


def shift_letter(char: str, shift: int) -> str:
    """Shift a lowercase character forward by shift positions with wrap-around."""
    # Calculate 0-25 offset, add shift, wrap around using modulo 26, convert back to char
    base = ord("a")
    return chr((ord(char) - base + shift) % 26 + base)


def encode_word(word: str, shift: int) -> str:
    """Encode an entire lowercase word by shifting each letter using shift_letter."""
    encoded_chars = []
    for char in word:
        encoded_chars.append(shift_letter(char, shift))
    return "".join(encoded_chars)


def main() -> None:
    word = input("Enter a word to encode: ").strip().lower()
    shift = int(input("Enter a shift value: ").strip())
    result = encode_word(word, shift)
    print(f"Encoded word: {result}")


if __name__ == "__main__":
    main()
