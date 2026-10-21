## **Submit | Tuple-Based Number Guessing Game**

### **Objective**

Create a guessing game where a tuple stores a random set of numbers and the user attempts to guess them.

### **Instruction**

1. Import the `random` module and generate a tuple of **5 random integers between 1 and 20**:
   ```python
   numbers = tuple(random.randint(1, 20) for _ in range(5))
   ```

2. Allow the user **five attempts** to guess the correct combination of numbers:
   - On each attempt, ask the user to enter **five numbers separated by spaces**
   - Convert the input into a tuple of integers
   - Compare the guessed tuple to the original one:
     - If it matches exactly, print **"You guessed correctly!"**
     - If not, tell the user how many values matched in the correct positions

3. After five tries, print the correct answer and the percentage of match for their best attempt.

### **Sample Output**

```text
Attempt 1: Enter 5 numbers: 1 2 3 4 5
2 numbers matched in the correct position.

...

Sorry! The correct combination was: (3, 8, 15, 2, 17)
Your best match was 60%.
```

### **File Submission**

Submit your file as: `tuple_guess_game.py`

### **Grading Rubric (10 points)**

- **2 points** - Generates a tuple with random integers
- **3 points** - Accepts user input and converts it into a tuple
- **2 points** - Compares input to target tuple and gives feedback
- **2 points** - Tracks and displays best attempt with match percentage
- **1 point** - Code includes comments or a docstring; runs without syntax errors
