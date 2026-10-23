## **Submit | Log Line Analyzer**

### **Objective**

Practice reading structured data from a file, parsing components, and performing basic statistics.

### **Instruction**

You are given a file called `server_logs.txt`. Each line of the file represents a log message with a severity level and a message, separated by a pipe `|`:

```text
INFO|System boot complete
WARNING|Low disk space
ERROR|Failed to connect to database
INFO|New connection established
```

Your task:

1. Read each line from `server_logs.txt`.
2. Count how many times each severity level appears (`INFO`, `WARNING`, `ERROR`, etc.).
3. Identify the longest message (by character count).
4. Write your output to a new file named `log_summary.txt` in the following format:

```text
Log Summary
INFO: 2
WARNING: 1
ERROR: 1

Longest message: Failed to connect to database
```

### **File Submission**

Submit your file as: `log_analyzer.py`

### **Grading Rubric (10 points)**

- **2 points** - Reads input file and parses each line with `.split('|')`
- **2 points** - Uses a dictionary or counters to count severity levels
- **2 points** - Finds the longest log message
- **2 points** - Writes the result to a new file in the correct format
- **1 point** - Code includes at least one docstring or explanatory comment
- **1 point** - Code runs without syntax errors
