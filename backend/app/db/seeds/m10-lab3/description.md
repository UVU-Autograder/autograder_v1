## **Submit | Student Club Memberships Using Sets**

### **Objective**

Write a Python program that uses sets to manage student memberships in two different university clubs. You'll practice basic set operations such as union, intersection, difference, and set methods.

### **Instruction**

1. Create two sets:
   - `coding_club` - contains names of students in the coding club: `{"Alice", "Bob", "Charlie", "Dana"}`
   - `robotics_club` - contains names of students in the robotics club: `{"Charlie", "Eve", "Frank", "Bob"}`

2. Perform the following tasks:
   - Find and print the list of students who are in **both** clubs (intersection)
   - Find and print students who are in **only one** of the clubs (symmetric difference)
   - Find and print students who are in **only the coding club** (difference)
   - Find and print the **total unique students** involved in either club (union)

3. Add a new member `"Grace"` to the `coding_club` using a set method (`.add()`).

4. Remove `"Eve"` from `robotics_club` using a method that does **not raise an error** if the member isn't found (`.discard()`).

### **Sample Output**

```text
Students in both clubs: {'Charlie', 'Bob'}
Students in only one club: {'Alice', 'Dana', 'Eve', 'Frank'}
Students only in the coding club: {'Dana', 'Alice'}
All unique students: {'Charlie', 'Bob', 'Eve', 'Grace', 'Alice', 'Frank', 'Dana'}
```

### **File Submission**

Submit your file as: `student_club_sets.py`

### **Grading Rubric (10 points)**

- **2 points** - Creates and initializes two sets with student names
- **2 points** - Correctly finds and prints the intersection of two sets
- **2 points** - Correctly finds and prints symmetric difference and difference
- **2 points** - Adds and removes elements using `.add()` and `.discard()`
- **1 point** - Uses `.union()` or `|` to print all unique members
- **1 point** - Code includes a comment or docstring; runs without syntax errors
