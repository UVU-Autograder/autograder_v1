# Module 3: Lab 4 - Properties

# Lab 4: Properties and Validation

## Objectives

In this lab, you will:

- Use the built-in `property()` function to define a property with a getter and setter
    
- Use the `@property` decorator to define a property
    
- Implement a read-only property
    
- Raise exceptions to validate input values
    

Starter Code

You are provided with a `Book` class that includes two private attributes: `_title` and `_author`.

class Book:  
    def __init__(self, title, author):  
        self._title = title  
        self._author = author  
​  
    def __str__(self):  
        return f"{self._title} by {self._author}"  
​  
def main():  
    my_book = Book("Book", "Author")  
​  
if __name__ == "__main__":  
    main()


## Part 1 – `title` Property (35 points)

1. (30 points) Create a `title` property using the built-in `property()` function.
    
    - In the setter method, raise a `TypeError` if the input is not a string.
        
    - Raise a `ValueError` if the input is an empty string.
        
    - If the input is a valid non-empty string, update the private title variable.
2. (5 points) In the `main()` function, update the book’s title to your favorite book.
    

## Part 2 – `author` Property (35 points)

1. (30 points) Define an `author` property using the `@property` decorator.
    
    - In the setter, raise a `TypeError` if the input is not a string.
        
    - Raise a `ValueError` if the input is an empty string.
        
    - If the input is a valid non-empty string, update the private author variable.
2. (5 points) In the `main()` function, update the book’s author to match the book title you chose in Part 1, and print the updated book. The output should look like:
    
    Harry Potter by J.K. Rowling
    

## Part 3 – Read-Only Property `description` (30 points)

1. (20 points) Define a read-only property `description` that returns a string in the format:
    
    Harry Potter was written by J.K. Rowling.
    
    You may implement this using either the `property()` function or the `@property` decorator.
    
2. (10 points) In the `main()` function:
    
    - Print the book’s description using the following code:
        
        print(my_book.description)
        
    - Try modifying the `description` property using the following code:
        
        my_book.description = f"{my_book.title} is a book written by {my_book.author}"
        
        Reflect question: What happens when you attempt to modify a read-only property? Write your explanation in a `Lab4_reflection.md.md` or `Lab4_reflection.md``.pdf` file.
        

## What to Submit

Submit the following files to Canvas:

- `book.py`: your completed class definition and `main()` function
    
- `Lab4_reflection.md` or `Lab4_reflection.pdf`: includes your answer to the reflection question in Part 3