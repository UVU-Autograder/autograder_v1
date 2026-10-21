## **Submit | Student Scorebook with Dictionary**

### **Objective**

Write a Python program that manages student scores using a dictionary. You'll create, update, access, and remove items using standard dictionary operations.

### **Instruction**

1. Create an empty dictionary called `scorebook`.

2. Add the following key-value pairs manually:
   - `scorebook["Alice"] = 88`
   - `scorebook["Bob"] = 75`
   - `scorebook["Charlie"] = 93`
   - `scorebook["Dana"] = 80`

3. Perform the following tasks:
   - **Print** all student names and scores using a `for` loop with `.items()`
   - **Update** Dana's score to 85
   - **Delete** Bob from the dictionary using `.pop()`
   - **Check** if `"Eve"` is in the dictionary using `.get()` and print a message accordingly
   - **Print** the average score of all remaining students

### **Sample Output**

```text
Alice: 88
Bob: 75
Charlie: 93
Dana: 80

Updated Dana's score to 85
Removed Bob from the scorebook
Eve not found in scorebook.
Average score: 88.67
```

### **File Submission**

Submit your file as: `student_scorebook.py`

### **Grading Rubric (10 points)**

- **2 points** - Initializes and populates a dictionary correctly
- **2 points** - Uses `.items()` and `for` loop to print contents
- **2 points** - Updates and removes entries using `.pop()` or `del`
- **2 points** - Uses `.get()` or `in` for checking key existence
- **1 point** - Calculates and prints the average score
- **1 point** - Includes a comment or docstring explaining purpose; runs without errors
