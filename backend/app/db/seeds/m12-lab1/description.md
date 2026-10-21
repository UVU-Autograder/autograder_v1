## **Submit | Generate UVUnacci Series Using Recursion**

### **Objective**

Recursion is a fundamental concept used to solve many algorithmic problems. You've previously explored how to solve the **Fibonacci sequence** recursively and understand how it grows by summing the last two terms.

Unlike Fibonacci, which sums the last **two** numbers, UVUnacci sums the last **three** to produce the next number:

- UVU(0) = 0
- UVU(1) = 1
- UVU(2) = 2
- UVU(3) = 0 + 1 + 2 = 3
- UVU(4) = 1 + 2 + 3 = 6
- UVU(5) = 2 + 3 + 6 = 11
- UVUnacci(n) = UVUnacci(n-1) + UVUnacci(n-2) + UVUnacci(n-3), for n >= 3

### **Instruction**

1. Define a **recursive function** `uvunacci_recursive(n)` that:
   - Returns the `n`-th term of the UVUnacci sequence
   - Defines the base cases before performing recursive calls

2. In your main code:
   - Use a loop or list comprehension to generate the first **30 terms** of the sequence using the recursive function
   - Print the resulting sequence

### **Sample Output**

```text
UVUnacci (first 30 terms):
[0, 1, 2, 3, 6, 11, 20, 37, 68, 125, 230, 423, 778, 1431, 2632, ...]
```

### **File Submission**

Submit your file as: `uvunacci_recursive.py`

### **Grading Rubric (10 points)**

- **3 points** - Defines a recursive function with correct base cases and recurrence relation
- **2 points** - Uses loop or comprehension to build the full sequence
- **2 points** - Correct output of sequence terms
- **2 points** - Uses comments or docstring to explain the function logic
- **1 point** - Code runs without syntax errors
