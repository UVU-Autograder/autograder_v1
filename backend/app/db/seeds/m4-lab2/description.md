## **Submit | Even or Odd Checker with Loop and Exit Option**

### **Objective**

Write a Python script that repeatedly allows the user to check whether a number is even or odd, or quit the program.

### **Instruction**

- Use a **loop** (e.g., `while` loop) to continuously prompt the user for an action until they choose to quit.
- Inside the loop:
  - Prompt the user to enter a character option:
    - `"c"` - Continue: check if a number is even or odd
    - `"q"` - Quit: exit the program
  - If the user enters `"c"`:
    - Ask for a **number**
    - Use conditionals to check whether the number is **even or odd**
    - Print a message such as:
      - `"The number 4 is even."`
      - `"The number 7 is odd."`
  - If the user enters `"q"`:
    - Print `"Program terminated."` and exit the loop
- The program should repeat until the user enters `"q"`.

### **Sample Interaction**

`Enter option ("c" to check, "q" to quit): c  `
`Enter a number: 5  `
`The number 5 is odd.`

`Enter option ("c" to check, "q" to quit): c  `
`Enter a number: 16  `
`The number 16 is even.`

`Enter option ("c" to check, "q" to quit): q  `
`Program terminated.`

### **File Submission**

Submit your file as: `even_odd_checker.py`

### **Grading Rubric (10 points)**

- **2 points** - Prompts user for option ("c" or "q")
- **2 points** - Uses a loop to repeat the prompt until "q" is entered
- **2 points** - Accurately checks and identifies even vs. odd numbers
- **2 points** - Displays clear and well-formatted output
- **1 point** - Code includes at least one comment or docstring
- **1 point** - Code runs without syntax errors
