## **Submit | Product Rating Analyzer (Map, Filter, Reduce, Lambda, Function Comprehension)**

### **Objective**

Use Python's functional programming features--including `lambda`, `map()`, `filter()`, `reduce()`, and **function-based comprehensions**--to analyze product review scores.

### **Instruction**

1. Start with the following list of product review scores (1 to 5):
   ```python
   ratings = [4, 5, 2, 3, 5, 1, 4, 3, 5, 2, 4]
   ```

2. **Use `map()` with a `lambda`** to:
   - Convert each numeric rating into a description string:
     - 5 -> `"Excellent"`, 4 -> `"Good"`, 3 -> `"Average"`, 2 -> `"Poor"`, 1 -> `"Terrible"`

3. **Use `filter()` with a `lambda`** to:
   - Extract ratings that are 4 or 5 (positive ratings)

4. **Use `reduce()` from `functools` with a `lambda`** to:
   - Compute the total and average rating

5. **Define a function called `generate_recommendation_flags(ratings)`** that:
   - Returns a **list of Boolean values** using **function comprehension**
   - Each value should be `True` if the rating is 4 or 5, otherwise `False`

6. **Define another function called `rating_summary(ratings)`** that:
   - Returns a **dictionary comprehension** with keys as ratings (1-5) and values as the **count of each rating**

7. In your main script:
   - Call all the above functions
   - Print the outputs clearly

### **Sample Output**

```text
Original Ratings: [4, 5, 2, 3, 5, 1, 4, 3, 5, 2, 4]
Descriptions: ['Good', 'Excellent', 'Poor', 'Average', 'Excellent', 'Terrible', 'Good', 'Average', 'Excellent', 'Poor', 'Good']
Positive Ratings: [4, 5, 5, 4, 5, 4]
Average Rating: 3.55
Recommendation Flags: [True, True, False, False, True, False, True, False, True, False, True]
Rating Summary: {1: 1, 2: 2, 3: 2, 4: 3, 5: 3}
```

### **File Submission**

Submit your file as: `product_rating_analyzer.py`

### **Grading Rubric (10 points)**

- **1 point** - Code includes helpful comments or docstrings
- **2 points** - Uses `map()` with `lambda` to convert ratings to descriptions
- **2 points** - Uses `filter()` to extract positive ratings
- **2 points** - Uses `reduce()` to calculate total and average
- **2 points** - Uses function comprehensions inside `generate_recommendation_flags()` and `rating_summary()`
- **1 point** - Clear output formatting and readability
