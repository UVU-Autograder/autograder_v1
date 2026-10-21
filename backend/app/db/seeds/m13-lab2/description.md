## **Submit | Build a Student Record System Using Objects**

### **Objective**

Create a simple **Student** class to model student records using Object-Oriented Programming. Practice creating objects, using constructors and instance methods, storing objects in a list, and displaying information using the `__str__()` method.

### **Instruction**

- **Create a `Student` class** with:
  - Attributes: `name`, `student_id`, `major`, `gpa` (float or int)
  - `__init__()` to initialize all attributes
  - `__str__()` method so printing a Student object displays:
    ```text
    Alice Johnson (ID: 10235)
    Major: Computer Science
    GPA: 3.85
    ```

- **Create the following instance methods:**
  - `update_gpa(new_gpa)` - Updates the student's GPA
  - `change_major(new_major)` - Updates the student's major
  - `display_summary()` - Prints a one-line summary of the student

- **In your `main()` function**:
  - Create at least **three Student objects**
  - Store the students in a **list**
  - Update the GPA of one student
  - Change the major of another student
  - Display all students using a loop
  - Print one student's complete information using `print()`

### **Sample Output**

```text
Student Summary

Alice Johnson - Computer Science - GPA: 3.85
Brian Lee - Information Systems - GPA: 3.42
Sophia Martinez - Software Engineering - GPA: 3.95

Updating GPA...
Alice Johnson - Computer Science - GPA: 3.95

Changing Major...
Brian Lee - Computer Science - GPA: 3.42

Complete Student Information

Alice Johnson (ID: 10235)
Major: Computer Science
GPA: 3.95
```

### **File Submission**

- Submit your file as: `student_oop_records.py`

### **Grading Rubric (10 points)**

- **2 pts** - Defines the `Student` class with appropriate attributes
- **2 pts** - Proper use of `__init__()` and `__str__()`
- **2 pts** - Implements and uses instance methods correctly
- **2 pts** - Creates multiple objects, stores them in a list, and displays them using a loop
- **2 pts** - Includes comments/docstrings and runs without syntax errors
