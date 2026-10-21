"""Project 2: Lost Language Decoder - Lexicon Rebuilder 7X."""


def encode_message(message: str, shift: int) -> str:
    """Encode a message by shifting alphabetic characters forward by shift positions."""
    effective_shift = shift % 26
    encoded_chars = []
    for char in message:
        if "a" <= char <= "z":
            shifted = chr((ord(char) - ord("a") + effective_shift) % 26 + ord("a"))
            encoded_chars.append(shifted)
        elif "A" <= char <= "Z":
            shifted = chr((ord(char) - ord("A") + effective_shift) % 26 + ord("A"))
            encoded_chars.append(shifted)
        else:
            encoded_chars.append(char)
    return "".join(encoded_chars)


def decode_message(message: str, shift: int) -> str:
    """Decode a message by shifting alphabetic characters backward by shift positions."""
    return encode_message(message, -shift)


def main() -> None:
    """Execute the interactive Caesar Cipher translation tool."""
    message = input("Enter a message: ")
    shift = int(input("Enter shift value: ").strip())

    mode = ""
    while mode not in ("e", "d"):
        mode = input("Choose (e)ncode or (d)ecode: ").strip().lower()

    if mode == "e":
        result = encode_message(message, shift)
        print(f"Encoded message: {result}")
    else:
        result = decode_message(message, shift)
        print(f"Decoded message: {result}")


if __name__ == "__main__":
    main()
