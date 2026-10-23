## **Submit | Fix the Student Registration System**

### **Objective**

Practice debugging techniques, testing strategies, and code improvement by identifying and fixing errors in an existing Python program.

### **Instruction**

You are given a partially completed Python program that manages student registrations. The program should allow users to:

- Add student names to a class list.
- Remove a student from the class list.
- Search for a student.
- Display the current class roster.
- Exit the menu loop cleanly.

Your task is to debug and improve the program:

- Identify and fix the following errors:
  - Syntax errors
  - Runtime errors (such as `ValueError` on removing non-existent students)
  - Logic errors (such as inverted search conditions or infinite loops)

- Handle validation and edge cases:
  - Empty student names (`Error: Student name cannot be empty.`)
  - Removing a student who does not exist
  - Non-numeric or invalid menu choices

- Improve code quality:
  - Improve variable and function names (e.g. `remove_student`, `search_student`)
  - Add comments and docstrings explaining important sections
  - Clean up formatting and remove unneeded dead code

### **Sample Output**

```text
Student Registration System
1. Add Student
2. Remove Student
3. Search Student
4. Display Class Roster
5. Exit
Enter Choice: 1
Enter student name: Alex
Student added successfully!

Enter choice: 4
Current Class Roster:
--------------------
Alex
Maria
John
```

Invalid input example:
```text
Enter student name:
Error: Student name cannot be empty.
```

### **File Submission**

- Submit your file as: `student_registration_fixed.py`

### **Grading Rubric (10 points)**

- **2 pts** - Fixes syntax, indentation, and logic errors from the buggy version
- **2 pts** - Includes validation / testing for edge and boundary cases
- **2 pts** - Program functionality: all 5 options work correctly
- **2 pts** - Formatted roster display, complete menu, and clean exit
- **2 pts** - Code includes comments/docstrings and uses clean snake_case naming conventions
