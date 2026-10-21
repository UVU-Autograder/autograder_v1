## **Submit | Course Enrollment System Using Nested Dictionaries**

### **Objective**

Write a Python program that simulates a simple course enrollment system. Use **nested dictionaries** to store and manage student data, and apply several dictionary methods (`.get()`, `.keys()`, `.values()`, `.items()`, `.pop()`, `.update()`).

### **Instruction**

1. Create a nested dictionary named `students`, where each key is a student ID (e.g., `"S001"`, `"S002"`) and the value is another dictionary containing:
   - `"name"` - student's name
   - `"major"` - student's major
   - `"courses"` - a list of enrolled course codes
   Example:
   ```python
   students = {
       "S001": {"name": "Alice", "major": "CS", "courses": ["CS1400", "MATH1210"]},
       "S002": {"name": "Bob", "major": "IS", "courses": ["INFO2410", "CS1400"]},
       "S003": {"name": "Charlie", "major": "DS", "courses": ["STAT1040", "CS1400"]},
   }
   ```

2. Define a function `print_student_info(student_id)` that:
   - Accepts a student ID
   - Uses `.get()` to retrieve the record safely
   - Prints name, major, and enrolled courses clearly

3. Define a function `enroll_student(student_id, course_code)` that:
   - Adds a course to a student's course list (avoid duplicates)
   - Uses `.setdefault()` or `.update()` as needed

4. Define a function `drop_student(student_id)` that:
   - Completely removes a student from the dictionary using `.pop()`

5. In the main part of your script:
   - Print all student IDs using `.keys()`
   - Call each function at least once to demonstrate functionality
   - Use `.items()` to display a summary of all students

### **Sample Output**

```text
Student IDs: dict_keys(['S001', 'S002', 'S003'])

Student Info (S001):
Name: Alice
Major: CS
Courses: ['CS1400', 'MATH1210']

Enrolled Alice in CS2600.
Dropped student S002.

Summary:
S001 → Alice (CS) → ['CS1400', 'MATH1210', 'CS2600']
S003 → Charlie (DS) → ['STAT1040', 'CS1400']
```

### **File Submission**

Submit your file as: `course_enrollment.py`

### **Grading Rubric (10 points)**

- **2 points** - Initializes a nested dictionary to model student records
- **2 points** - Defines and uses `print_student_info()` with `.get()`
- **2 points** - Defines `enroll_student()` and modifies nested list with `.setdefault()` or `.update()`
- **2 points** - Defines `drop_student()` and uses `.pop()` correctly
- **1 point** - Uses `.keys()`, `.items()`, or `.values()` to display data
- **1 point** - Code includes clear comments or docstrings; runs without syntax errors
