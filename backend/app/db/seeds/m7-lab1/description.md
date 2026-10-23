## **Submit | Random Text File Generator**

### **Objective**

Create a Python script that generates random text made of lowercase words and writes it into a file using modular functions.

### **Instruction**

Write a Python program consisting of the following three functions:

1. **`make_word()`** - Returns a randomly generated word
   - Word length is randomly selected between **5 and 10 characters**
   - Each character is a **random lowercase letter** from `'a'` to `'z'`

2. **`make_line()`** - Returns a string made up of **8 to 10 random words**
   - Use `make_word()` to generate each word
   - Words are separated by a **single space**

3. **`write_random_text()`** - Writes **at least 100 lines** to a file named `randomText.txt`
   - Each line is created using `make_line()`
   - Make sure each line ends with a **newline character (`\n`)**
   - The output file should contain readable, randomly generated content

### **Sample Output: first 3 of 100+ lines, illustrative only**

```text
lqvpx ztqfuw stepu mhqkv rzuuikc mdxvgo njskz bjmvv
kqzai ixlzv yvduq qzqspw slvns nnpoc fhfmeo sgozi rpgmx
zkvgh qhnkz ywdkl kcmvl xffqj mzqetj uiphc
```

Each line will vary due to randomness but must follow the required format.

### **File Submission**

Submit your file as: `random_text_generator.py`

### **Grading Rubrics (10 points)**

- **2 points** - `make_word()` returns a lowercase word with length between 5-10 characters
- **2 points** - `make_line()` returns a line with 8-10 space-separated random words
- **4 points** - `write_random_text()` writes 100+ lines to `randomText.txt`, each ending with `\n`
- **1 point** - Code includes at least one **comment or docstring** explaining the logic
- **1 point** - Code runs without syntax errors
