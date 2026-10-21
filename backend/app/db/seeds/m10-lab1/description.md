## **Submit | Word Frequency Counter Using Dictionary**

### **Objective**

Create a simple word frequency counter that uses a dictionary to tally word occurrences in a given string.

### **Instruction**

1. Define a function `word_count(text)` that:
   - Accepts a string of text as input
   - Splits the text into words using `.split()`
   - Creates a dictionary where:
     - Each **key** is a word (lowercased)
     - Each **value** is the number of times the word appears
   - Uses `.get()` or `if` checks to build the dictionary without using `collections.Counter`

2. In your main script:
   - Call the function with a sample paragraph
   - Print each word and its frequency using a `for` loop and `.items()`
   - Remove any word that appears **only once** using a loop and `.copy()` to avoid modifying the dictionary during iteration
   - Print the dictionary after removal

### **Sample Output**

```text
Original Word Frequencies:
the: 3
dog: 2
barked: 2
loudly: 1
ran: 1

After removing words with only one occurrence:
the: 3
dog: 2
barked: 2
```

### **File Submission**

Submit your file as: `word_frequency.py`

### **Grading Rubric (10 points)**

- **2 points** - Correctly tokenizes the input text and creates the frequency dictionary
- **3 points** - Uses `.get()` or `in` to build word counts without error
- **2 points** - Prints dictionary contents using `.items()`
- **2 points** - Removes single-occurrence entries using a proper method (e.g., `.copy()` during deletion)
- **1 point** - Code is documented with comments or docstrings; runs without syntax errors
