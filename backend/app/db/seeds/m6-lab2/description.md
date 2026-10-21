## **Submit | Interleave Odd and Even Integer Lists**

### **Objective**

Write a Python function that takes two lists of integers--one with odd numbers and one with even numbers--and returns a new list where the values are interleaved in alternating order.

### **Instruction**

- In your script, create two predefined lists:
  - `odds = [11, 33, 55]`
  - `evens = [22, 44, 66, 88]`

- Define a function called `interleave(odds, evens)` that:
  - Accepts two list parameters
  - Returns a new list interleaving values from both lists: **odd, even, odd, even, ...**
  - Does **not modify the original lists**
  - Returns (does not print) the final list

- In your main code:
  - Call the `interleave()` function using the `odds` and `evens` lists
  - Print the resulting interleaved list clearly

### **Sample Input / Output**

**Sample Code:**
```python
odds = [11, 33, 55]
evens = [22, 44, 66, 88]

result = interleave(odds, evens)
print("Interleaved list:", result)
```

**Output:**
```text
Interleaved list: [11, 22, 33, 44, 55, 66, 88]
```

### **File Submission**

Submit your file as: `interleave_lists.py`

### **Grading Rubric (10 points)**

- **2 points** - Two lists (`odds` and `evens`) are correctly created
- **2 points** - `interleave(odds, evens)` function is defined with two parameters
- **3 points** - Function returns a correctly interleaved list
- **1 point** - Result is printed in the main script in a clear format
- **1 point** - Includes a comment or docstring explaining the logic
- **1 point** - Code runs without syntax errors
