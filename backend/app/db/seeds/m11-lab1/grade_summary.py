"""Module 11 Lab 1: Grade Summary Generator Using Nested Functions and Scopes."""


def calculate_average(grades: list[float | int]) -> float | str:
    """Calculate average of grades; return 'N/A' if empty."""
    if not grades:
        return "N/A"
    return sum(grades) / len(grades)


def process_grades(grades: list[float | int]) -> tuple[list[float | int], float | str, dict[str, int]]:
    """Filter grades, compute average, and return letter grade distribution via inner function."""
    # Filter valid grades (0 to 100) using list comprehension
    valid_grades = [g for g in grades if 0 <= g <= 100]

    def grade_distribution() -> dict[str, int]:
        """Compute counts of grades by letter, accessing valid_grades from enclosing scope."""
        dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for g in valid_grades:
            if g >= 90:
                dist["A"] += 1
            elif g >= 80:
                dist["B"] += 1
            elif g >= 70:
                dist["C"] += 1
            elif g >= 60:
                dist["D"] += 1
            else:
                dist["F"] += 1
        return dist

    avg = calculate_average(valid_grades)
    distribution = grade_distribution()
    return valid_grades, avg, distribution


def main() -> None:
    sample_grades = [95, 82, -10, 76, 59, 89, 101]
    valid_grades, avg, distribution = process_grades(sample_grades)

    print(f"Valid grades: {valid_grades}")
    if isinstance(avg, (int, float)):
        print(f"Average grade: {avg:.1f}")
    else:
        print(f"Average grade: {avg}")
    print(f"Grade distribution: {distribution}")


if __name__ == "__main__":
    main()
