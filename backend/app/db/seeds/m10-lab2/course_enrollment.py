"""Module 10 Lab 2: Course Enrollment System Using Nested Dictionaries."""

students = {
    "S001": {"name": "Alice", "major": "CS", "courses": ["CS1400", "MATH1210"]},
    "S002": {"name": "Bob", "major": "IS", "courses": ["INFO2410", "CS1400"]},
    "S003": {"name": "Charlie", "major": "DS", "courses": ["STAT1040", "CS1400"]},
}


def print_student_info(student_id: str) -> None:
    """Print student info using .get() for safe dictionary lookup."""
    info = students.get(student_id)
    if not info:
        print(f"Student {student_id} not found.")
        return
    print(f"Student Info ({student_id}):")
    print(f"Name: {info['name']}")
    print(f"Major: {info['major']}")
    print(f"Courses: {info['courses']}")


def enroll_student(student_id: str, course_code: str) -> None:
    """Add a course to a student's course list avoiding duplicates."""
    info = students.get(student_id)
    if info:
        courses = info.setdefault("courses", [])
        if course_code not in courses:
            courses.append(course_code)
        print(f"Enrolled {info['name']} in {course_code}.")


def drop_student(student_id: str) -> None:
    """Completely remove a student record using .pop()."""
    removed = students.pop(student_id, None)
    if removed:
        print(f"Dropped student {student_id}.")


def main() -> None:
    print(f"Student IDs: {students.keys()}\n")

    print_student_info("S001")
    print()

    enroll_student("S001", "CS2600")
    drop_student("S002")
    print()

    print("Summary:")
    for sid, info in students.items():
        print(f"{sid} -> {info['name']} ({info['major']}) -> {info['courses']}")


if __name__ == "__main__":
    main()
