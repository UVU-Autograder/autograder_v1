## **Submit | Weighted Movement and Frequency Counter (Sophie's Pattern)**

### **Objective**

Introduce biased/random movement and analyze the directional frequency.

### **Instruction**

Write a program that simulates 200 steps of biased movement, where:

1. The character always starts at `(0, 0)`.

2. Movement is weighted:
   - 50% chance to move **Up**
   - 16.67% each for **Down**, **Left**, and **Right**

3. Use `random.choices()` with weights.

4. For each direction taken, count how many times it was chosen.

5. Print:
   - Final (x, y) position
   - Count of each direction

### **Sample Output**

```text
Final position: (2, 94)
Direction counts:
Up: 102
Down: 31
Left: 33
Right: 34
```

### **File Submission**

- Submit your Python file as: `sophie_biased_walk.py`

### **Grading Rubric (10 points)**

- **2 pts** - Uses `random.choices()` with correct weights
- **2 pts** - Tracks and updates position in each step
- **2 pts** - Maintains count of each direction
- **2 pts** - Displays final coordinates and stats
- **2 pts** - Clear code organization and comments
