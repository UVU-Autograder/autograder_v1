"""Module 8 Lab 1: Analyze Student Grades Using Tuples."""


def analyze_grades(student_data: list[tuple[str, int | float]]) -> tuple[float, int | float, str, int | float, str]:
    """Calculate average, highest grade with student, and lowest grade with student."""
    if not student_data:
        return (0.0, 0, "", 0, "")

    total = sum(grade for _, grade in student_data)
    average = total / len(student_data)

    highest = max(student_data, key=lambda s: s[1])
    lowest = min(student_data, key=lambda s: s[1])

    return (average, highest[1], highest[0], lowest[1], lowest[0])


def main() -> None:
    # List of student tuples (name, grade)
    students = [("Alice", 87), ("Bob", 92), ("Charlie", 78), ("Dana", 85)]

    avg_grade, high_grade, high_name, low_grade, low_name = analyze_grades(students)

    print(f"Average grade: {avg_grade:.1f}")
    print(f"Highest grade: {high_grade} ({high_name})")
    print(f"Lowest grade: {low_grade} ({low_name})")


if __name__ == "__main__":
    main()
