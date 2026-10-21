## **Submit | Build a Simple Library Using Objects**

### **Objective**

Create a simple **Book** class to model library books using Object-Oriented Programming. Practice creating objects, writing constructors and methods, storing objects in a list, and displaying object information using the `__str__()` method.

### **Instruction**

- **Create a `Book` class** with the following:
  - Attributes: `title`, `author`, `year`, `available` (bool, default True)
  - `__init__()` to initialize all attributes (Constructor)
  - `__str__()` method to return a readable string like:
    ```text
    'The Pragmatic Programmer' by Andrew Hunt (1999) [Available]
    ```

- **Add the following instance methods** to the `Book` class:
  - `borrow()` - sets `available = False` and prints a confirmation message
  - `return_book()` - sets `available = True` and prints a confirmation message
  - `is_available()` - returns True if the book is available

- In your `main()` function:
  - Create 3 `Book` objects
  - Store the books in a list
  - Borrow one book
  - Return the same book
  - Use a loop to display all books by printing each object

### **Sample Output**

```text
Book borrowed: Clean Code
Book returned: Clean Code

Library Collection:
'Clean Code' by Robert Martin (2008) [Available]
'Atomic Habits' by James Clear (2018) [Available]
'Deep Work' by Cal Newport (2016) [Available]
```

### **File Submission**

Submit your file as: `library_system.py`

### **Grading Rubric (10 points)**

- **2 pts** - Defines the `Book` class correctly
- **2 pts** - Proper use of `__init__()`, `__str__()`
- **2 pts** - Implements and uses instance methods (`borrow()` and `return_book()`)
- **2 pts** - Creates multiple objects, stores them in a list, and displays them using a loop
- **2 pts** - Code includes helpful comments/docstrings and runs without errors
