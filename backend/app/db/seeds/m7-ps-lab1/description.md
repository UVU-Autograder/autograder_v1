## **Submit | Generate and Save Number Series to File**

### **Objective**

Create a Python program that generates a series of numbers using a loop, stores them in a list, and writes the list to a text file -- one number per line.

### **Instruction**

Write a program that:

1. Prompts the user for three inputs:
   - **Starting number**
   - **Ending number**
   - **Step size**

2. Uses a `for` loop to create a list of numbers starting from the starting number, increasing by the step size, and stopping at or before the ending number.

3. Stores all generated numbers in a **Python list**.

4. Writes the list to a file named `number_series.txt`, with **each number on a new line**.

### **Example Run**

```text
Enter starting number: 10
Enter ending number: 100
Enter step size: 15

Saved 7 numbers to number_series.txt
```

**Contents of `number_series.txt`**:
```text
10
25
40
55
70
85
100
```

### **File Submission**

Submit your file as: `save_number_series.py`

### **Grading Rubric (10 points)**

- **2 points** - Uses `input()` to collect starting, ending, and step values
- **2 points** - Uses a `for` loop to generate the sequence correctly
- **2 points** - Stores the numbers in a **list** before writing
- **2 points** - Writes all numbers to a text file with one number per line
- **2 points** - Includes a final print message and at least one comment; runs without errors
