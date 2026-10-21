## **Project 5: Pathfinder Tracker - Space Walk Simulation**

### **Mission Brief**

In the **Exodus: Humanity's Rebirth** mission, astronauts regularly perform spacewalks to inspect and repair critical systems aboard the generation ship.

Mission Control needs a tracking system to monitor each astronaut's movement during a spacewalk. Represent each astronaut as an **object** using Object-Oriented Programming.

### **Project Description**

Create an **Astronaut** class and simulate the spacewalks of three astronauts: **Lance**, **Sophie**, and **Finn**.

Each astronaut maintains their own information and is visualized using the provided plotting function:

- **Lance:** Moves randomly in any direction (Up, Down, Left, Right) with equal probability. Movements are represented by **blue circles** (`color='b'`, `marker='o'`).
- **Sophie:** Prefers to move upward, with approximately a **50% chance** of moving Up and equal probabilities (16.67%) of moving Down, Left, or Right. Movements are represented by **red squares** (`color='r'`, `marker='s'`).
- **Finn:** Moves only horizontally (Left or Right) with equal probability. Movements are represented by **green triangles** (`color='g'`, `marker='^'`).

### **Tasks**

1. **Create the Astronaut Class**:
   - Attributes: `name`, `color`, `marker`, `positions` (list of coordinate tuples, starting at `[(0, 0)]`).
   - Constructor `__init__(name, color, marker)`
   - String representation `__str__()` returning name, current position, and total recorded positions.
   - Instance method `move(dx, dy)` updating current position and appending to `positions`.

2. **Simulate Movement**:
   - Create three Astronaut objects (Lance, Sophie, Finn).
   - Simulate **500 movement steps** for each astronaut using the `move()` method.
   - Store all astronaut objects in a list.

3. **Visualize Movement**:
   - Call `plot_pathfinder_walk()` for each astronaut.
   - Produce three images: `Lance_spacewalk.png`, `Sophie_spacewalk.png`, and `Finn_spacewalk.png`.

### **File Submission**

Submit your Python file as: `pathfinder_tracker.py`

### **Grading Criteria (100 points)**

- **30 pts** - Movement patterns for Lance, Sophie, and Finn implemented correctly
- **20 pts** - Output produces randomized, unique paths on successive runs
- **20 pts** - Astronaut class structure and coordinate list tracking
- **15 pts** - Loops and helper functions used to prevent repeated code
- **5 pts** - Main function with conditional execution guard (`if __name__ == "__main__":`)
- **5 pts** - Encapsulated state with limited global scope
- **5 pts** - Code style, comments, and docstrings
