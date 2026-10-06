# Module 4: Programming Project - Dessert Shop 2 Using Classes in main

Read instructions carefully. Not following instructions will result in you not receiving the credit you want.

Make sure your output matches the sample run.

**Big Note:** The starting point for Part 2 is the file you submitted for Part 1.

# Objectives

In Part 2 you will learn the following:

- Use existing classes to build an application
    
- Add console output to manually test your application
    
- Create manual test cases to test your application by inspection
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `DessertItem`
            
        - `Candy`
            
        - `Cookie`
            
        - `IceCream`
            
        - `Sundae`
            
        - `Order` (new)
            
- Module name: `dessertshop` (new)
    
    - Functions
        
        - `main`
            

# Problem

A Dessert Shop sells candy by the pound, cookies by the dozen, ice cream by the scoop, and sundaes (ice cream with a topping).

In Part 2, implement the ability to create an order consisting of items available at the Dessert Shop to what you already did in Part 1. These items include Candy, Cookies, Ice Cream, and Sundaes. You will also implement a main function with a simple console user interface to interactively test the order entry system.

# Order Class

The `Order` class is a list-like container for DessertItem objects.

The `Order` class has the following attribute and methods:

- Attributes:
    
    - `order`: list of `DessertItem` objects
        
- Methods:
    
    - A constructor that takes **no arguments** other than `self` and creates an **empty** order.
        
    - `add(item)`: Takes a  `DessertItem` and adds it to the `order` list.
        
    - `__len__()` : Returns the number of items in the order.
        
    - `__iter__()`: Returns an iterator for the order.
        
    - `__next__()`: Returns the next item when iterating over the order.
        

# main()

`main` should do the following:

- Create a new instance of the order class
    
- Add the following items to the order:
    
    Candy("Candy Corn", 1.5, .25)  
    Candy("Gummy Bears", .25, .35)  
    Cookie("Chocolate Chip", 6, 3.99)  
    IceCream("Pistachio", 2, .79)  
    Sundae("Vanilla", 3, .69, "Hot Fudge", 1.29)  
    Cookie("Oatmeal Raisin", 2, 3.45)
    
- Print out just the name of each DessertItem in the order
    
- Print out the total number of items in the order
    

# UML Diagram

![UML](image.png)

The class diagram above adds a design for an `Order` in the system and the `main()` method that is the application driver. The classes show attributes with associated data types. `main()` is in the `dessertshop` module.

UML (Unified Modeling Language) is the de facto industry standard modeling tool for object-oriented programming worldwide.

# Key Program Requirements

1. Dessert Shop 2 extends the functionality of Dessert Shop 1
    
2. The `Order` class is implemented as above.
    
3. Program output looks exactly like the example run.
    
4. You submit 2 code files in your Codio workspace: `dessert.py`, and `dessertshop.py`.
    

# Example Run

Candy Corn  
Gummy Bears  
Chocolate Chip  
Pistachio  
Vanilla  
Oatmeal Raisin  
Total number of items in order: 6

# Grading

**Note: Dessert Shop 2 must include all the code from Dessert Shop 1.**

This exercise is manually graded. Use the following rubric for grading.

| Criteria                       | Mastery (100%)                                                                                                                                                                                                | Proficient (85%)                                                                                             | Developing (70%)                                                                                        | Beginning (60%)                                                                                                   | Not Demonstrated (50%)                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Order Class Structure**      | The `Order` class is correctly implemented with an attribute that is a list of DessertItem objects. The constructor, which takes no arguments other than `self`, correctly initializes an empty Order.        | The `Order` class mostly meets requirements but has minor issues in constructor or attributes.               | The `Order` class partially meets requirements but has significant issues in constructor or attributes. | The `Order` class has been attempted, but it is fundamentally flawed.                                             | The `Order` class does not exist.                               |
| **Order Class Methods**        | The `Order` class correctly implements the `add(item)` method, `__len__()`, `__iter__()` and `__next__()` magic methods. All methods work correctly.                                                          | Most of the required methods in the `Order` class are implemented correctly but there are minor issues.      | Some of the required methods in the `Order` class are implemented correctly but there are major issues. | The required methods in the `Order` class have been attempted, but they are fundamentally flawed.                 | Required methods in the `Order` class are not implemented.      |
| **Main Function**              | The `main` function correctly creates an instance of the Order class, adds the required items to the order, and correctly prints out the name of each DessertItem in the order and the total number of items. | The `main` function does most of the required tasks correctly but has minor issues.                          | The `main` function does some of the required tasks correctly but has major issues.                     | The `main` function has been attempted but it is fundamentally flawed.                                            | The `main` function is not implemented.                         |
| **Program Output**             | The program's output exactly matches the example output given in the problem statement.                                                                                                                       | The program's output mostly matches the example output, with minor discrepancies.                            | The program's output somewhat matches the example output, but there are major discrepancies.            | The program's output has been attempted but it significantly deviates from the example output.                    | The program does not produce output.                            |
| **Integration of Part 1 Code** | Part 2 correctly builds on Part 1 and includes all relevant code from the previous assignment.                                                                                                                | Part 2 includes most of the code from Part 1 with minor omissions.                                           | Part 2 includes some code from Part 1 but lacks important components.                                   | Part 2 includes very little from Part 1 or the integration is unclear.                                            | Part 2 does not appear to build on Part 1 at all.               |
| **Code Quality**               | Code is clearly written, logically organized, and easy to follow. No syntax errors.                                                                                                                           | Code is mostly clear and logically organized, with minor syntax errors that do not affect program execution. | Code is somewhat clear and organized, but with syntax errors that may affect program execution.         | Code is unclear, disorganized, and contains numerous syntax errors that prevent program from executing correctly. | No code or code cannot be evaluated due to major syntax errors. |

In this rubric, each criterion is evaluated independently and contributes to the overall score for the assignment.

For example, if a student's code has mastery level "Order Class Structure" (60 points), proficient "Order Class Methods" (51 points), developing "Main Function" (42 points), beginning "Program Output" (36 points), developing "Integration of Part 1 Code" (42 points),and proficient "Code Quality" (51 points), the student's total score would be the average of these six scores.

# What to Submit

Upload your `dessert.py` and `dessertshop.py`to Canvas.