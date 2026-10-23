## **Archive Reconstruction System - "LORE Vault Recompiler"**

### **Learning Outcomes**

In completing this project, you will be able to:

- Read structured input from text files using Python file handling.
- Write structured output to text files in a specified format.
- Process structured string data and extract useful metadata.
- Use and manipulate data structures like lists, tuples, and dictionaries.
- Sort and rearrange data to make it usable.
- Compute basic statistics like average string length.

### **Mission Brief**

After Earth's collapse, the last fragments of human knowledge were loaded into encrypted storage vaults aboard the **Nova Exodus** fleet. These archives, known as **LORE (Legacy of Recorded Earth)**, were saved in partial, scrambled form. Each file represents a single digital book or manual crucial for rebuilding civilization on **Nova Terra**, the fleet's destination.

Each archived book was tagged with a three-letter identifier (e.g., ALG, TTL, WOO) and fragmented into scrambled lines. Now, your mission is to write the software -- **LORE Vault Recompiler** -- that processes these files, reorders them, analyzes their structure, and produces reconstructed versions to be stored in the colony's permanent memory banks.

### **Project Description**

You are given a set of book archive files, each named as `<BOOKCODE>.txt`, such as `TTL.txt`. Each line in the file contains a line of text and its original line number, separated by a vertical bar (`|`):

```text
"It was the best of times, it was the worst of times,"|1
```

However, these lines are out of order. Your task is to:

1. Read the contents of the scrambled archive file.
2. Reconstruct the correct order of the lines by sorting based on their line numbers.
3. Identify the longest line in the book (if multiple lines tie, choose the one with the higher line number).
4. Compute the average line length (rounded to the nearest integer).
5. Write all this information into a new file named `<BOOKCODE>_book.txt`, structured as follows:

```text
<BOOKCODE>
Longest line (<line_number>): <longest line text>
Average length: <average_length>
<ordered book content lines go here>
```

**Your Program Must:**

- Accept a single archive file from the command line (`python3 lore_vault.py TTL.txt`).
- Parse each line for content and line number.
- Sort the lines based on their line number.
- Identify the longest line using both length and tie-breaking by higher line number.
- Calculate the average line length, rounded to the nearest whole number.
- Write the structured output into a new file `<BOOKCODE>_book.txt`.

### **File Submission**

Submit your file as: `lore_vault.py`

### **Key Program Requirements and Rubrics (100 points)**

- **40 points** - File Generation for Given Files: Produces correctly reconstructed output file
- **40 points** - File Generation for Unknown Files: Works accurately for unknown scrambled archives
- **10 points** - Main Function with Conditional Execution (`if __name__ == "__main__":`)
- **5 points** - No Global Code
- **5 points** - Snake Case / camelCase code style
