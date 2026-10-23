## **Submit | Character Shifter - Forward and Reverse**

### **Objective**

Create a basic letter-shifting utility that can shift any alphabetical character forward or backward by a fixed amount, similar to the Caesar cipher.

### **Instruction**

- Define a function `shift_character(char, shift, mode)` that:
  - Takes a single character (`char`), an integer shift value, and a mode (`"forward"` or `"backward"`).
  - If the character is a letter, it shifts it by the `shift` value while preserving case.
  - If the character is non-alphabetic, it returns the character unchanged.

- In your main code:
  - Prompt the user to enter a single letter.
  - Ask for the shift value and direction (forward/backward).
  - Call the function and print the result.

### **Sample Interaction**

`Enter a character: A  `
`Enter shift value: 3  `
`Enter direction (forward/backward): forward  `
`Shifted character: D`

### **File Submission**

- Submit a file named: `character_shifter.py`

### **Grading Rubric (10 points)**

- **3 pts** - Function correctly handles uppercase and lowercase letters
- **2 pts** - Preserves non-alphabet characters as-is
- **2 pts** - Input from user and function call is correct
- **2 pts** - Code uses f-string and clear formatting
- **1 pt** - Runs without syntax error
