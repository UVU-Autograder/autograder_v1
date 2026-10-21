"""Module 7 Problem Solving Lab 1: Generate and Save Number Series to File."""


def main() -> None:
    # Prompt user for start, end, and step size
    start = int(input("Enter starting number: ").strip())
    end = int(input("Enter ending number: ").strip())
    step = int(input("Enter step size: ").strip())

    # Generate sequence and store in a list
    numbers = []
    for num in range(start, end + 1, step):
        numbers.append(num)

    # Write each number on a new line to number_series.txt
    with open("number_series.txt", "w", encoding="utf-8") as f:
        for num in numbers:
            f.write(f"{num}\n")

    print(f"Saved {len(numbers)} numbers to number_series.txt")


if __name__ == "__main__":
    main()
