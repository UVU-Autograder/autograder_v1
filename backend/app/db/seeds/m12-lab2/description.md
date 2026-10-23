## **Submit | Optimize UVUnacci Using Memoization and Iteration**

### **Objective**

In the last assignment, you used **pure recursion** to compute the UVUnacci sequence, which becomes inefficient for larger values due to **repeated calculations** and **exponential time complexity**.

In this assignment, you'll address that inefficiency using two classic optimization strategies:

- **Top-down approach (memoization)**
- **Bottom-up approach (iteration)**

### **Instruction**

Enhance your UVUnacci program by doing the following:

#### a. Create Two New Functions:

1. `uvunacci_memoized(n, memo_dict)`
   - Uses recursion with **manual memoization** (do not use `@lru_cache`)
   - Stores and reuses previously computed values in a dictionary

2. `uvunacci_iterative(n)`
   - Uses a **loop** to compute the UVUnacci sequence efficiently

#### b. Create a `main()` function that:

- Computes and prints the results using each of the three methods:
  - `uvunacci_recursive(n)`
  - `uvunacci_memoized(n, memo_dict)`
  - `uvunacci_iterative(n)`
- Measures execution time for each approach using `time.time()` or `time.perf_counter()`

#### c. Provide a short summary of your results:

- Which method was fastest?
- How does memoization improve over naive recursion?
- Why is the iterative version most efficient?

### **Sample Output**

```text
Generating UVUnacci(25)...
Recursive:      2145013 -> Time: 0.246200 seconds
Memoized:       2145013 -> Time: 0.000120 seconds
Iterative:      2145013 -> Time: 0.000003 seconds

Summary:
- Iterative and memoized approaches are significantly faster than naive recursion.
- Memoization avoids exponential repeated sub-problem calculations.
- Iteration is most efficient because it avoids recursion call stack overhead.
```

### **File Submission**

- Submit your file as: `uvunacci_optimized.py`

### **Grading Rubric (10 points)**

- **1 point** - Uses baseline recursive function
- **3 points** - Implements memoized version correctly
- **3 points** - Implements an efficient iterative version
- **1 point** - Uses `time.time()` or `time.perf_counter()` to measure execution time
- **1 point** - Outputs are clearly printed and compared
- **1 point** - Includes docstrings or comments
