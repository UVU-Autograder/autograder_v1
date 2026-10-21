## **Submit | Grade Summary Generator Using Nested Functions and Scopes**

### **Objective**

Write a Python program that calculates and summarizes student performance using helper functions, inner functions, variable scope, and list comprehension.

### **Instruction**

1. Define a **main function** called `process_grades(grades)` that:
   - Accepts a list of **numeric grades** (0-100)
   - Uses a **list comprehension** to filter out invalid grades (e.g., `< 0` or `> 100`)
   - Calls helper functions to perform calculations and return a formatted summary

2. Create a **helper function** `calculate_average(grades)` that:
   - Returns the average of the list
   - If the list is empty, return `"N/A"`

3. Inside `process_grades()`, define an **inner function** `grade_distribution()` that:
   - Returns a dictionary with counts of grades by letter:
     - `'A'`: 90-100
     - `'B'`: 80-89
     - `'C'`: 70-79
     - `'D'`: 60-69
     - `'F'`: below 60
   - This function should access the outer function's `valid_grades` list via closure

4. In the main script:
   - Call `process_grades()` with a hardcoded list of grades (e.g., `[95, 82, -10, 76, 59, 89, 101]`)
   - Print the result in a readable format (e.g., average and letter distribution)

### **Sample Output**

```text
Valid grades: [95, 82, 76, 59, 89]
Average grade: 80.2
Grade distribution: {'A': 1, 'B': 2, 'C': 1, 'D': 0, 'F': 1}
```

### **File Submission**

Submit your file as: `grade_summary.py`

### **Grading Rubric (10 points)**

- **2 points** - Uses a helper function to calculate the average with proper edge case handling
- **2 points** - Filters invalid grades using list comprehension
- **2 points** - Defines and uses an inner function to calculate grade distribution
- **2 points** - Demonstrates understanding of variable scopes (e.g., closure access in nested function)
- **1 point** - Final result is printed in a clear and formatted way
- **1 point** - Includes at least one docstring or explanatory comment; runs without syntax errors
