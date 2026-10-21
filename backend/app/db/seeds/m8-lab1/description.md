## **Submit | Analyze Student Grades Using Tuples**

### **Objective**

Write a Python program that stores student names and grades using tuples, then analyzes the data to print summary statistics.

### **Instruction**

- Create a list of **tuples**, where each tuple contains:
  - A student's name (string)
  - Their final grade (integer or float)
  Example:
  ```python
  students = [("Alice", 87), ("Bob", 92), ("Charlie", 78), ("Dana", 85)]
  ```

- Define a function called `analyze_grades(student_data)` that:
  - Accepts the list of tuples as input
  - Calculates:
    - The **average grade**
    - The **highest and lowest grades**
    - The names of the students with the highest and lowest grades
  - Returns all of this information as a new tuple

- In your main code:
  - Call the function and print the returned results in a formatted message

### **Sample Output**

```text
Average grade: 85.5
Highest grade: 92 (Bob)
Lowest grade: 78 (Charlie)
```

### **File Submission**

Submit your file as: `analyze_student_grades.py`

### **Grading Rubric (10 points)**

- **2 points** - Stores student name/grade pairs as tuples
- **3 points** - `analyze_grades()` correctly computes average, min, and max
- **2 points** - Properly returns and unpacks a tuple from the function
- **2 points** - Formatted and informative output is printed in the main script
- **1 point** - Code includes at least one comment or docstring; runs without syntax errors
