"""Student Dataclass - Lab 7 Model Solution."""

from dataclasses import dataclass, field


@dataclass(order=True)
class Student:
    """Models a college student using a dataclass with ID ordering."""

    id: int
    name: str
    major: str
    courses: list[str] = field(default_factory=list, compare=False)

    def enroll(self, course: str) -> None:
        """Enroll student in a course by adding course number to list."""
        self.courses.append(course)

    def total_courses(self) -> int:
        """Return total number of enrolled courses."""
        return len(self.courses)


def main() -> None:
    """Main testing entrypoint."""
    s1 = Student(101, "Alice Smith", "Computer Science")
    s2 = Student(102, "Bob Jones", "Software Engineering")
    s3 = Student(100, "Charlie Brown", "Data Science")

    s1.enroll("CS 1410")
    s1.enroll("CS 2300")
    s2.enroll("CS 1400")

    print(s1)
    print(f"{s1.name} total courses: {s1.total_courses()}")
    print(s2)

    print(f"s1 > s2: {s1 > s2}")
    print(f"s3 < s1: {s3 < s1}")

    students = [s1, s2, s3]
    sorted_students = sorted(students)
    print("Sorted students by ID:", [s.id for s in sorted_students])


if __name__ == "__main__":
    main()
