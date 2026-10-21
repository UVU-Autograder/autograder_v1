## **Submit | Student Grade Management System**

### **Objective**

Practice program design, functional decomposition, debugging, and testing by creating a Python program that manages student grades using functions, input validation, and test cases.

### **Instruction**

Create a Python program that manages student grades for a class. Your program should store student names and grades using appropriate Python data structures (such as lists or dictionaries).

- **Design Your Program**:
  - Create a plan or pseudocode describing:
    - What information the program needs to store
    - What tasks the program should perform
    - What functions are needed to complete each task (e.g. `add_student()`, `calculate_average()`, `find_student()`, `display_report()`)
  - Include this design in comments or docstrings at the beginning of your script.

- **Implement the Program Using Functions**:
  - Add student names and grades to your data structure.
  - Calculate the average grade for the class.
  - Find a student's grade using their name.
  - Display a summary report of student information.

- **Add Input Validation**:
  - Handle invalid grade entries (e.g. text instead of numbers).
  - Prevent grades outside the valid range (0-100).
  - Handle cases where a student name does not exist.
  - Prevent crashes using `try/except` and conditional checks.

- **Debug and Test Your Program**:
  - Provide test cases testing:
    - Normal Inputs (valid names and grades)
    - Boundary Values (grades 0 and 100)
    - Invalid Inputs (non-numeric, > 100, < 0)
    - Edge Cases (missing student, empty list/dict)

### **Sample Output**

```text
Enter student name: Alex
Enter grade: 92
Student added successfully!
Enter student name: Maya
Enter grade: 85
Student added successfully!

Class Report:
--------------------
Alex: 92
Maya: 85
Class Average: 88.5

Search for student: Alex
Alex's grade: 92

Enter grade: abc
Invalid input. Please enter a number between 0 and 100.
```

### **File Submission**

- Submit your file as: `student_grade_manager.py`

### **Grading Rubric (10 points)**

- **2 pts** - Program Design (clear plan/pseudocode in comments before coding)
- **3 pts** - Program Implementation (functions perform specific tasks correctly)
- **2 pts** - Debugging and Error Handling (handles invalid input, bounds, try/except)
- **2 pts** - Testing (includes test cases for normal, boundary, invalid, and edge cases)
- **1 pt** - Code Quality (meaningful names, docstrings/comments, clean run)
