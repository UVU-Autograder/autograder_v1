## **Submit | Word Encoder - Shift All Letters**

### **Objective**

Use a function and a loop to apply a basic Caesar-style letter shift to an entire word. This version **only encodes** a single word and assumes lowercase input.

### **Instruction**

- Define a function `shift_letter(char, shift)` that:
  - Accepts a single lowercase alphabetical character.
  - Returns the character shifted forward by `shift` positions.
  - Wraps around from `'z'` to `'a'` as needed (e.g., `'y'` shifted by 3 becomes `'b'`).

- Define another function `encode_word(word, shift)` that:
  - Uses a loop to apply `shift_letter()` to every character in `word`.
  - Returns the encoded word as a string.

- In your main script:
  - Ask the user to input a single lowercase word (e.g., `"hello"`).
  - Ask for a positive integer shift value.
  - Use `encode_word()` to transform the word.
  - Print the encoded result.

### **Sample Interaction**

```text
Enter a word to encode: hello
Enter a shift value: 2
Encoded word: jgnnq
```

### **File Submission**

Submit your file as: `simple_word_encoder.py`

### **Grading Rubric (10 points)**

- **3 pts** - Defines a valid `shift_letter()` function with wrap-around logic
- **3 pts** - Defines `encode_word()` and correctly uses a loop and helper function
- **2 pts** - User input and output are handled with clarity
- **1 pt** - Code includes at least one comment explaining how the shift works
- **1 pt** - Code runs without syntax errors
