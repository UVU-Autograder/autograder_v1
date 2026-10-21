## **Project Submission**

### **Learning Outcomes**

In completing this project, you will learn how to:

- Apply basic string manipulation techniques in Python.
- Use loops and conditionals to process and transform character data.
- Create custom encryption and decryption functions using Caesar Cipher logic.
- Handle both uppercase and lowercase letters, preserving formatting and spacing.

### **Mission Briefing**

In the final days of Earth, as global communication systems failed, small resistance groups developed a cipher to encode their survival knowledge. Their records, now known as the *Old Earth Cipher*, included techniques on farming, medicine, and civil order -- all crucial to humanity's rebirth.

Just before Earth was lost, these encrypted texts were uploaded to Nova Gaia's deep data vaults.

Now, decades later aboard the Nova Exodus colony ship, you must implement **Lexicon Rebuilder 7X**, a Caesar Cipher-based translation tool. This software allows colonists to both encrypt and decrypt lost data transmissions by shifting characters according to a numerical key -- reviving critical knowledge buried in code.

### **Problem Statement**

You are to build a Caesar Cipher simulator with two main features: encoding and decoding. The cipher works by shifting each alphabetical character by a user-defined number. For encoding, letters are shifted forward; for decoding, they are shifted backward. The program should:

- Prompt the user to enter a message and a shift value.
- Ask whether the message should be encoded or decoded.
- Transform each letter appropriately while **preserving case** (uppercase/lowercase).
- **Ignore** and preserve non-alphabetic characters like spaces, punctuation, and numbers.
- Display the final encoded or decoded message.

**Your Program Must**

- Implement a function to encode a message by shifting characters forward.
- Implement a function to decode a message by shifting characters backward.
- Use loops and conditionals to check character types and apply the cipher.
- Preserve spacing, numbers, and punctuation in the final message.
- Accept user input and print clearly labeled output using f-strings.

### **Example Run**

**Example 1: Encoding a Message**
```text
Enter a message: attack at dawn
Enter shift value: 3
Choose (e)ncode or (d)ecode: e
Encoded message: dwwdfn dw gdzq
```

**Example 2: Decoding a Message**
```text
Enter a message: dwwdfn dw gdzq
Enter shift value: 3
Choose (e)ncode or (d)ecode: d
Decoded message: attack at dawn
```

**Example 3: Handling Non-Alphabet Characters**
```text
Enter a message: secure data 123!
Enter shift value: 4
Choose (e)ncode or (d)ecode: e
Encoded message: wigyvi hexe 123!
```

### **File Submission**

Submit your file as: `lost_language_decoder.py`

### **Key Program Requirements and Rubrics (100 points)**

- **30 points** - String Transformation: Works with sample text and ciphering
- **30 points** - String Transformation for Unknown Text: Works with different unknown texts and ciphers
- **5 points** - For Loop: Uses at least one for loop in the code
- **5 points** - While Loop: Uses at least one while loop in the code
- **5 points** - If Statement: Has at least one if statement in the code
- **5 points** - Functions for Encode and Decode: Defines functions for encoding and decoding
- **10 points** - Main Function: Program contains a main function with conditional execution (`if __name__ == "__main__":`)
- **10 points** - Snake or Camel Case: All variable names and code follow Python snake_case or camelCase
