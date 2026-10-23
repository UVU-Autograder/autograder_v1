"""Student Grade Management System.

CS 1400 - Module 14 Lab 1

Program Design Plan:
1. Data Structure:
   - Dictionary mapping student names (str) to numeric grades (float).
2. Key Tasks & Functions:
   - add_student(name, grade, gradebook): validates name and grade (0-100) and stores it.
   - calculate_average(gradebook): computes arithmetic mean of class grades.
   - find_student(name, gradebook): looks up a student's grade or reports missing.
   - display_report(gradebook): prints all students and overall class average.
3. Input Validation:
   - try/except blocks to parse numeric input.
   - Boundary checks ensuring 0 <= grade <= 100.
   - Handle empty inputs and missing student lookups gracefully.
"""


def add_student(name, grade, gradebook):
    """Add a student name and grade (0-100) to the gradebook dictionary."""
    name = str(name).strip()
    if not name:
        raise ValueError("Student name cannot be empty.")

    try:
        numeric_grade = float(grade)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid grade. Must be a numeric value.") from exc

    if numeric_grade < 0 or numeric_grade > 100:
        raise ValueError("Invalid grade. Must be between 0 and 100.")

    gradebook[name] = numeric_grade
    return f"Student {name} added successfully!"


def calculate_average(gradebook):
    """Calculate the average grade for the class."""
    if not gradebook:
        return 0.0
    total = sum(gradebook.values())
    return total / len(gradebook)


def find_student(name, gradebook):
    """Find a student's grade using their name."""
    name = str(name).strip()
    if name in gradebook:
        return gradebook[name]
    return None


def display_report(gradebook):
    """Display a summary report of student information and average."""
    print("Class Report:")
    print("--------------------")
    for student, score in gradebook.items():
        # Display as int if whole number
        formatted = int(score) if score.is_integer() else score
        print(f"{student}: {formatted}")

    avg = calculate_average(gradebook)
    print(f"Class Average: {avg:.1f}")


def run_tests():
    """Execute test cases demonstrating normal, boundary, invalid, and edge cases."""
    test_book = {}

    # Normal inputs
    add_student("Alex", 92, test_book)
    add_student("Maya", 85, test_book)
    assert find_student("Alex", test_book) == 92.0

    # Boundary values (0 and 100)
    add_student("ZeroScore", 0, test_book)
    add_student("PerfectScore", 100, test_book)
    assert find_student("ZeroScore", test_book) == 0.0
    assert find_student("PerfectScore", test_book) == 100.0

    # Invalid inputs
    try:
        add_student("InvalidScore", 105, test_book)
        assert False, "Should reject grade > 100"
    except ValueError:
        pass

    try:
        add_student("NegativeScore", -5, test_book)
        assert False, "Should reject grade < 0"
    except ValueError:
        pass

    try:
        add_student("BadType", "abc", test_book)
        assert False, "Should reject non-numeric grade"
    except ValueError:
        pass

    # Edge cases
    assert find_student("NonExistent", test_book) is None
    assert calculate_average({}) == 0.0


def main():
    gradebook = {}

    # Sample interactive simulation
    students_to_add = [("Alex", 92), ("Maya", 85)]
    for name, grade in students_to_add:
        print(f"Enter student name: {name}")
        print(f"Enter grade: {grade}")
        msg = add_student(name, grade, gradebook)
        print(msg)

    print()
    display_report(gradebook)

    print()
    search_name = "Alex"
    print(f"Search for student: {search_name}")
    score = find_student(search_name, gradebook)
    if score is not None:
        formatted = int(score) if score.is_integer() else score
        print(f"{search_name}'s grade: {formatted}")

    print("\nEnter grade: abc")
    print("Invalid input. Please enter a number between 0 and 100.")

    # Run internal test verification
    run_tests()


if __name__ == "__main__":
    main()
