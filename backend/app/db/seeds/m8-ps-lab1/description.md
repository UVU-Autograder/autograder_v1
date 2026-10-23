## **Submit | Message Sorter & Length Stats**

### **Objective**

Build skills for handling line-based structured input, tuple sorting, and computing text statistics.

### **Instruction**

You are given a file called `quotes_data.txt`. Each line has a quote followed by an author ID, separated by a `|`:

```text
The only way to do great work is to love what you do.|A39
Life is what happens when you're busy making other plans.|A14
In the middle of every difficulty lies opportunity.|A20
The future belongs to those who believe in the beauty of their dreams.|A10
Believe you can and you're halfway there.|A29
```

Your task:

1. Read all lines from the file and store them as a list of tuples `(quote_text, author_id)`.

2. Sort the quotes by:
   - First: Length of the quote (longest first)
   - Second: Alphabetical order of author ID (if tie)

3. Compute and display:
   - Total number of quotes
   - Average quote length (rounded to nearest integer)
   - Quote with the most words

4. Store the results in a file named `sorted_quotes.txt`. The content of that file looks like:

```text
Sorted Quotes
========================================
What lies behind us and what lies before us are tiny matters compared to what lies within us. | A09
Do not go where the path may lead, go instead where there is no path and leave a trail. | A09
Success is not final, failure is not fatal: It is the courage to continue that counts. | A32
...
Statistics
========================================
Total quotes: 50
Average quote length: 54
Quote with most words: Do not go where the path may lead, go instead where there is no path and leave a trail.
```

### **File Submission**

Submit your file as: `quote_sort_stats.py`

### **Grading Rubric (10 points)**

- **2 points** - Parses lines into tuples using `.split('|')`
- **2 points** - Sorts list using quote length and tie-breaker rule
- **2 points** - Correctly calculates average quote length
- **2 points** - Identifies quote with most words using `.split()`
- **1 point** - Uses at least one user-defined function
- **1 point** - Code runs without syntax errors and uses clear variable names
