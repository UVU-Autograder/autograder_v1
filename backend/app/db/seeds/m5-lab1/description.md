## **Submit | Area of a Regular Pentagon**

### **Objective**

Write two Python functions to calculate the area of a single regular pentagon and the total area of multiple pentagons using parameterized functions.

### **Instruction**

1. **Define the function** `areaRegularPentagon(lengthSide)`:
   - Accepts one integer or float parameter: `lengthSide`
   - Computes the area using the formula:
     $$\text{Area} = \frac{5 \times \text{side}^2}{4 \times \tan\left(\frac{\pi}{5}\right)}$$
   - Uses `math.pi` and `math.tan`
   - Returns the area as a floating-point number (do not print)
   - Add at least one **comment or docstring** explaining the formula and function.

2. **Define the function** `areaMultiplePentagons(numPentagons, lengthSide)`:
   - Accepts two integer or numeric parameters:
     - `numPentagons`: number of regular pentagons
     - `lengthSide`: side length of each pentagon
   - Calls `areaRegularPentagon(lengthSide)` to compute the area of one pentagon
   - Returns the **total area** (i.e., `numPentagons × area of one`)

3. **Do not duplicate the formula** in `areaMultiplePentagons`; it must reuse the `areaRegularPentagon()` function.

### **Sample Function Call / Output**

```python
total = areaMultiplePentagons(3, 7)
print(f"Total area for 3 pentagons with side 7: {total:.4f}")
```

**Output:**

```text
Total area for 3 pentagons with side 7: 252.9101
```

### **File Submission**

- Submit your file as: `area_multiple_pentagons.py`
- This file should include both:
  - `areaRegularPentagon(lengthSide)`
  - `areaMultiplePentagons(numPentagons, lengthSide)`

### **Grading Rubric (10 points)**

- **2 points** - Defines `areaMultiplePentagons(numPentagons, lengthSide)`
- **3 points** - Correctly calls `areaRegularPentagon(lengthSide)` instead of duplicating the formula
- **3 points** - Returns the correct total area
- **1 point** - Includes a docstring or comment explaining the relationship between the functions
- **1 point** - Code runs without syntax errors
