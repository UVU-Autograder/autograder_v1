## **Submit | Count Vowels in randomText.txt**

### **Objective**

Write a Python program that reads the contents of a text file and counts the occurrences of each vowel (a, e, i, o, u, y), regardless of case.

### **Instruction**

1. Define a function that:
   - Reads the file **`randomText.txt`**
   - Processes every **word on every line**
   - Counts the number of occurrences of **each vowel**: `a`, `e`, `i`, `o`, `u`, `y`
   - Treats uppercase and lowercase letters the same (i.e., case-insensitive)
   - Returns the counts to the caller (can be a dictionary or tuple of values)

2. In the **main script**:
   - Call the vowel-counting function
   - Store the returned values in variables
   - Print the result in a **clear, formatted message**

3. Use **try/except** to handle file errors gracefully (e.g., if the file is missing)

### **Sample Output**

```text
There were 134 a's, 142 e's, 87 i's, 92 o's, 55 u's, and 61 y's.
```

*(This is an illustrative format; actual counts will reflect the file provided.)*

### **File Submission**

Submit your file as: `count_vowels.py`

### **Grading Rubric (10 points)**

- **2 points** - Defines a function that reads `randomText.txt` and returns counts for a, e, i, o, u, y
- **3 points** - Correctly counts all six vowels, case-insensitively
- **2 points** - Caller unpacks the result and prints a clearly formatted summary
- **1 point** - Handles missing file errors using `try/except`
- **1 point** - Includes at least one **comment or docstring** explaining the logic
- **1 point** - Code runs without syntax errors
