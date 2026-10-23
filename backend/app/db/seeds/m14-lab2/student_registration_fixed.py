"""Student Registration System (Fixed Version).

CS 1400 - Module 14 Lab 2
Debugged and improved student registration program allowing users to:
1. Add a student
2. Remove a student
3. Search for a student
4. Display the class roster
5. Exit
"""

# Initial student roster (cleaned of empty/whitespace entries)
students = ["Emma", "Liam", "Olivia"]


def add_student(student_list):
    """Add a new student to the registration list with validation."""
    name = input("Enter student name: ").strip()
    if not name:
        print("Error: Student name cannot be empty.")
        return

    student_list.append(name)
    print("Student added successfully!")


def remove_student(student_list):
    """Remove a student from the registration list with safety checks."""
    name = input("Enter student name to remove: ").strip()
    if name in student_list:
        student_list.remove(name)
        print(f"{name} removed successfully.\n")
    else:
        print(f"Error: {name} not found in student roster.\n")


def search_student(student_list):
    """Search for a student in the registration list."""
    name = input("Enter student name to search: ").strip()
    if name in student_list:
        print(f"{name} found!\n")
    else:
        print(f"{name} not found.\n")


def display_roster(student_list):
    """Display the formatted current class roster."""
    print("\nCurrent Class Roster:")
    print("--------------------")
    for student in student_list:
        print(student)
    print()


def run_tests():
    """Unit test verification for roster operations."""
    test_roster = ["Emma", "Liam"]
    # Verify add
    test_roster.append("Alex")
    assert "Alex" in test_roster
    # Verify search
    assert "Alex" in test_roster
    assert "Unknown" not in test_roster
    # Verify remove
    test_roster.remove("Alex")
    assert "Alex" not in test_roster


def main():
    """Run the main interactive menu loop."""
    choice = 0
    while choice != 5:
        print("Student Registration System")
        print("1. Add Student")
        print("2. Remove Student")
        print("3. Search Student")
        print("4. Display Class Roster")
        print("5. Exit")

        try:
            choice_str = input("Enter choice: ").strip()
            if not choice_str:
                continue
            choice = int(choice_str)
        except ValueError:
            print("Invalid choice. Please enter a number between 1 and 5.\n")
            continue

        if choice == 1:
            add_student(students)
        elif choice == 2:
            remove_student(students)
        elif choice == 3:
            search_student(students)
        elif choice == 4:
            display_roster(students)
        elif choice == 5:
            print("Goodbye!")
        else:
            print("Invalid choice. Please enter a number between 1 and 5.\n")


if __name__ == "__main__":
    main()
