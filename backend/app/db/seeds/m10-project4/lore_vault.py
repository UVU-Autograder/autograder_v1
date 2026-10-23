"""Project 4: Archive Reconstruction System - LORE Vault Recompiler."""

import sys
from pathlib import Path


def parse_archive(filename: str) -> list[tuple[str, int]]:
    """Parse scrambled archive into list of (line_text, line_number) tuples."""
    lines = []
    with open(filename, "r", encoding="utf-8") as f:
        for raw_line in f:
            raw_line = raw_line.rstrip("\r\n")
            if not raw_line or "|" not in raw_line:
                continue
            # Last occurrence of '|' separates text from line number
            idx = raw_line.rfind("|")
            text = raw_line[:idx]
            line_num = int(raw_line[idx + 1:].strip())
            lines.append((text, line_num))
    return lines


def find_longest_line(lines: list[tuple[str, int]]) -> tuple[str, int]:
    """Find the longest line in the book, breaking ties with higher line number."""
    if not lines:
        return "", 0
    # Key: (length of text, line number)
    return max(lines, key=lambda item: (len(item[0]), item[1]))


def compute_average_length(lines: list[tuple[str, int]]) -> int:
    """Compute average line length rounded to nearest whole number."""
    if not lines:
        return 0
    total_len = sum(len(item[0]) for item in lines)
    return round(total_len / len(lines))


def reconstruct_book(input_filename: str) -> str:
    """Reconstruct scrambled archive, write output file, and return output filename."""
    path_obj = Path(input_filename)
    book_code = path_obj.stem
    output_filename = str(path_obj.parent / f"{book_code}_book.txt")

    lines = parse_archive(input_filename)
    # Sort lines based on their original line number
    sorted_lines = sorted(lines, key=lambda item: item[1])

    longest_text, longest_num = find_longest_line(lines)
    avg_len = compute_average_length(lines)

    with open(output_filename, "w", encoding="utf-8") as out:
        out.write(f"{book_code}\n")
        out.write(f"Longest line ({longest_num}): {longest_text}\n")
        out.write(f"Average length: {avg_len}\n")
        for text, _ in sorted_lines:
            out.write(f"{text}\n")

    return output_filename


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python lore_vault.py <BOOKCODE.txt>")
        sys.exit(1)

    input_file = sys.argv[1]
    reconstruct_book(input_file)


if __name__ == "__main__":
    main()
