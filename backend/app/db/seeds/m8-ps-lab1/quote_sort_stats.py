"""Module 8 Problem Solving Lab 1: Message Sorter & Length Stats."""


def parse_quotes(filename: str = "quotes_data.txt") -> list[tuple[str, str]]:
    """Parse input file into a list of (quote, author_id) tuples."""
    quotes = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|")
            quotes.append((parts[0].strip(), parts[1].strip()))
    return quotes


def sort_quotes(quotes: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Sort quotes by length descending, with author_id ascending as tiebreaker."""
    return sorted(quotes, key=lambda q: (-len(q[0]), q[1]))


def compute_stats(quotes: list[tuple[str, str]]) -> tuple[int, int, str]:
    """Compute total quotes, rounded average length, and quote with most words."""
    total = len(quotes)
    if total == 0:
        return 0, 0, ""

    total_len = sum(len(q[0]) for q in quotes)
    avg_len = round(total_len / total)

    most_words_quote = max(quotes, key=lambda q: len(q[0].split()))[0]
    return total, avg_len, most_words_quote


def write_sorted_quotes(
    sorted_quotes: list[tuple[str, str]],
    total: int,
    avg_len: int,
    most_words_quote: str,
    output_filename: str = "sorted_quotes.txt",
) -> None:
    """Write sorted quotes and computed statistics to sorted_quotes.txt."""
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("Sorted Quotes\n")
        f.write("========================================\n")
        for quote, author in sorted_quotes:
            f.write(f"{quote} | {author}\n")
        f.write("\nStatistics\n")
        f.write("========================================\n")
        f.write(f"Total quotes: {total}\n")
        f.write(f"Average quote length: {avg_len}\n")
        f.write(f"Quote with most words: {most_words_quote}\n")


def main() -> None:
    quotes = parse_quotes("quotes_data.txt")
    sorted_q = sort_quotes(quotes)
    total, avg_len, most_words = compute_stats(sorted_q)
    write_sorted_quotes(sorted_q, total, avg_len, most_words)
    print("Processed quotes and saved to sorted_quotes.txt.")


if __name__ == "__main__":
    main()
