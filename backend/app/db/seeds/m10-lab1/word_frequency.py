"""Module 10 Lab 1: Word Frequency Counter Using Dictionary."""


def word_count(text: str) -> dict[str, int]:
    """Tally frequency of each lowercased word in text using dictionary operations."""
    counts = {}
    words = text.split()
    for word in words:
        clean_word = word.lower()
        counts[clean_word] = counts.get(clean_word, 0) + 1
    return counts


def main() -> None:
    sample_text = "the dog barked loudly the dog barked the ran"
    frequencies = word_count(sample_text)

    print("Original Word Frequencies:")
    for word, count in frequencies.items():
        print(f"{word}: {count}")

    # Remove single-occurrence entries using .copy()
    filtered = frequencies.copy()
    for word, count in frequencies.items():
        if count == 1:
            filtered.pop(word)

    print("\nAfter removing words with only one occurrence:")
    for word, count in filtered.items():
        print(f"{word}: {count}")


if __name__ == "__main__":
    main()
