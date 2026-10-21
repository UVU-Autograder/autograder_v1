## **Submit | Compute Areas of Geometric Shapes**

### **Objective**

Write a Python script that calculates the area of common geometric shapes using user-provided input and proper formulas.

### **Instruction**

Your script must calculate the area of the following shapes **in sequence**:

#### **Circle**

Formula:

Area = π × r²

Steps:
- Prompt the user to enter the radius
- Store the value in a variable
- Compute the area using `math.pi`
- Print the result using a clear, formatted message

#### **Rectangle**

Formula:

Area = width × height

Steps:
- Prompt the user to enter the width
- Prompt the user to enter the height
- Compute the area
- Print the result using a clear, formatted message

#### **Triangle**

Formula:

Area = (base × height) ÷ 2

Steps:
- Prompt the user to enter the base
- Prompt the user to enter the height
- Compute the area
- Print the result using a clear, formatted message

### **Formatting Requirements**

- Use `import math` to access π
- Display numeric results with **limited decimal places** (e.g., 4 decimals)
- Include **at least one comment** explaining part of your code

### **Sample Interaction**

`Enter the radius: 3.5  `
`The area of the circle with radius 3.5 is 38.4845  `

`Enter the width: 10  `
`Enter the height: 4  `
`The area of the rectangle 10 x 4 is 40.0000  `

`Enter the base: 6  `
`Enter the height: 8  `
`The area of the triangle with base 6 and height 8 is 24.0000`

### **File Submission**

Submit your file as: `compute_areas.py`

### **Grading Rubric (10 points)**

- **3 points** - Correctly prompts the user and stores input values
- **3 points** - Applies the correct formulas for all three shapes (must use `math.pi` for the circle)
- **2 points** - Outputs results with clear messages and proper formatting
- **1 point** - Includes at least one meaningful comment
- **1 point** - Code runs without syntax errors
