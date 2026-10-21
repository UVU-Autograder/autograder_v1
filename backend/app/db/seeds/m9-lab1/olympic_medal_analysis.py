"""Module 9 Lab 1: Country Medal Analysis Using Nested Tuples."""


def analyze_medals(data: list[tuple[str, tuple[int, int, int]]]) -> list[tuple[str, int]]:
    """Calculate total medals for each country and return sorted list descending."""
    results = []
    for country, medals in data:
        gold, silver, bronze = medals
        total = gold + silver + bronze
        results.append((country, total))

    # Sort descending by total medals
    return sorted(results, key=lambda x: x[1], reverse=True)


def find_most_gold(data: list[tuple[str, tuple[int, int, int]]]) -> str:
    """Find the country with the most gold medals using tuple indexing."""
    best_country = ""
    max_gold = -1
    for country, medals in data:
        gold = medals[0]
        if gold > max_gold:
            max_gold = gold
            best_country = country
    return best_country


def main() -> None:
    olympic_data = [
        ("USA", (10, 8, 6)),
        ("China", (8, 10, 5)),
        ("Germany", (5, 3, 4)),
        ("Japan", (6, 5, 7)),
    ]

    ranked = analyze_medals(olympic_data)

    print("Total Medal Counts:")
    for rank, (country, total) in enumerate(ranked, 1):
        print(f"{rank}. {country} - {total} medals")

    most_gold = find_most_gold(olympic_data)
    print(f"\nCountry with the most gold medals: {most_gold}")


if __name__ == "__main__":
    main()
