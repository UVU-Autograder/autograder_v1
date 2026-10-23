## **Submit | Country Medal Analysis Using Nested Tuples**

### **Objective**

Write a Python program to analyze Olympic medal counts using a list of nested tuples. Each tuple represents a country and its medal breakdown (gold, silver, bronze). You'll extract information, calculate totals, and rank the countries.

### **Instruction**

1. Create a list of tuples, where each tuple contains:
   - Country name (string)
   - Another tuple with medal counts: `(gold, silver, bronze)`
   Example:
   ```python
   olympic_data = [
       ("USA", (10, 8, 6)),
       ("China", (8, 10, 5)),
       ("Germany", (5, 3, 4)),
       ("Japan", (6, 5, 7)),
   ]
   ```

2. Define a function `analyze_medals(data)` that:
   - Accepts the list of tuples as input
   - Calculates total medals for each country (sum of gold, silver, bronze)
   - Returns a **new list of tuples**, where each tuple contains:
     - Country name
     - Total medal count
   - Sorts this list in descending order of total medals

3. In your main code:
   - Call the function
   - Print the sorted country list with their total medal counts
   - Also print the name of the country with the **most gold medals** (use tuple indexing to compare gold counts)

### **Sample Output**

```text
Total Medal Counts:
1. USA - 24 medals
2. China - 23 medals
3. Japan - 18 medals
4. Germany - 12 medals

Country with the most gold medals: USA
```

### **File Submission**

Submit your file as: `olympic_medal_analysis.py`

### **Grading Rubric (10 points)**

- **2 points** - Stores country names and medal counts using nested tuples
- **2 points** - Defines `analyze_medals()` and uses tuple unpacking
- **3 points** - Accurately calculates total medals and returns a sorted list
- **1 point** - Correctly identifies the country with the most gold medals
- **1 point** - Output is clearly formatted
- **1 point** - Code includes at least one comment or docstring; runs without syntax errors
