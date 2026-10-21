"""Build a Student Record System Using Objects.

CS 1400 - Module 13 Lab 2
Demonstrates object creation, attribute manipulation, instance methods,
collections of objects, and custom string representations for student records.
"""


class Student:
    """Represents an academic student record."""

    def __init__(self, name, student_id, major, gpa):
        """Initialize student attributes."""
        self.name = name
        self.student_id = student_id
        self.major = major
        self.gpa = float(gpa)

    def update_gpa(self, new_gpa):
        """Update the student's GPA."""
        self.gpa = float(new_gpa)

    def change_major(self, new_major):
        """Update the student's academic major."""
        self.major = new_major

    def display_summary(self):
        """Print a one-line summary of the student record."""
        print(f"{self.name} - {self.major} - GPA: {self.gpa:.2f}")

    def __str__(self):
        """Return multi-line or detailed string format."""
        return (
            f"{self.name} (ID: {self.student_id})\n"
            f"Major: {self.major}\n"
            f"GPA: {self.gpa:.2f}"
        )


def main():
    # Create 3 Student objects
    s1 = Student("Alice Johnson", 10235, "Computer Science", 3.85)
    s2 = Student("Brian Lee", 10236, "Information Systems", 3.42)
    s3 = Student("Sophia Martinez", 10237, "Software Engineering", 3.95)

    # Store in a list
    students = [s1, s2, s3]

    print("Student Summary\n")
    # Display summaries
    for s in students:
        s.display_summary()

    print("\nUpdating GPA...")
    s1.update_gpa(3.95)
    s1.display_summary()

    print("\nChanging Major...")
    s2.change_major("Computer Science")
    s2.display_summary()

    print("\nComplete Student Information\n")
    print(s1)


if __name__ == "__main__":
    main()
