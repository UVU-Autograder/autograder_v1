## **Submit | Simulate Random Grid Movement (Lance's Pattern)**

### **Objective**

Build a simple simulation of random 2D movement, storing positions step-by-step and visualizing the path.

### **Instruction**

Write a program that simulates a single astronaut's walk on a 2D grid:

1. The astronaut starts at position `(0, 0)`.

2. For **100 steps**, randomly move **Up, Down, Left, or Right**, each with equal probability.

3. Track each (x, y) coordinate after every step.

4. Print the final position.

5. Use **matplotlib** to plot the path taken as a line plot.

### **Sample Output**

```text
Final position after 100 steps: (-3, 5)
```

Plot: a path from the origin to the final position, showing the trajectory.

### **File Submission**

- Submit your Python file as: `random_walk_basic.py`

### **Grading Rubric (10 points)**

- **2 pts** - Uses `random.choice()` with 4 directions
- **2 pts** - Tracks positions using a list of tuples
- **2 pts** - Loop structure correctly updates position
- **2 pts** - Matplotlib plot clearly shows the path
- **2 pts** - Code includes comments and no syntax errors
