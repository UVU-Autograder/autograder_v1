## **Submit | UVU Bookstore Discount Calculator**

### **Objective**

You are visiting the **UVU Bookstore** to purchase a **noise-cancelling headphone**. The bookstore offers a **5% discount** to **students** and an **8% discount** to **faculty**.

Write a Python script that calculates the final price of an item based on the buyer's role (student or faculty) and applies the appropriate discount.

### **Instruction**

- Prompt the user to:
  - Enter the **item price** (a float or numeric input)
  - Enter the **buyer type** as:
    - `"s"` for student
    - `"f"` for faculty

- Based on the buyer type:
  - Apply a **5% discount** if the input is `"s"` (student)
  - Apply an **8% discount** if the input is `"f"` (faculty)

- Use **conditional statements** (`if`, `elif`, etc.) to determine the discount rate and compute the **final price**.

- Display the final price in a clear, formatted message.

### **Sample Interaction/ Output**

`Enter the item price: 120.00  `
`Enter buyer type ("s" for student, "f" for faculty): s  `
`Final price after 5% discount: $114.00`

`Enter the item price: 250  `
`Enter buyer type ("s" for student, "f" for faculty): f  `
`Final price after 8% discount: $230.00`

### **File Submission**

Submit your file as: `uvu_discount.py`

### **Grading Rubric (10 points)**

- **2 points** - Takes two user inputs: price and buyer type
- **2 points** - Correct discount rates are applied based on buyer type
- **2 points** - Final price is correctly calculated
- **2 points** - Output is formatted clearly and displays final price
- **1 point** - Code includes at least one comment or docstring
- **1 point** - Code runs without syntax errors
