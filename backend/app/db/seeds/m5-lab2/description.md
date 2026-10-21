## **Submit | Input Validation for Name and Age Using try / except**

### **Objective**

Write a Python script that collects a user's name and age with proper input validation. The script should continue prompting the user until both inputs are valid, then display a confirmation message.

### **Instruction**

- Prompt the user to enter:
  - Their **name**
  - Their **age**

- **Validation Requirements:**
  - **Name** must be:
    - A **non-empty string**
    - **Not purely numeric** (e.g., `"123"` is invalid)
  - **Age** must be:
    - A valid **integer**
    - Use `try/except` to catch invalid conversions (e.g., `"twenty"`)

- If either input is invalid, display an appropriate error message and re-prompt until both inputs are correct.

- Once both are valid, display a message like: `"Thanks, Alice! Your age is 21."`

### **Sample Interaction**

```text
Enter your name: 123
Invalid name. Please enter a non-numeric name.

Enter your name: Alice
Enter your age: twenty
Invalid age. Please enter an integer.

Enter your age: 21
Thanks, Alice! Your age is 21.
```

### **File Submission**

Submit your file as: `validate_name_age.py`

### **Grading Rubric (10 points)**

- **1 point** - Prompts for both name and age
- **3 points** - Uses `try/except` to validate that age is an integer
- **2 points** - Validates that name is a non-empty, non-numeric string
- **2 points** - Continues prompting until valid inputs are provided
- **1 point** - Displays a clear, formatted confirmation message
- **1 point** - Code includes at least one comment or docstring explaining the validation logic
