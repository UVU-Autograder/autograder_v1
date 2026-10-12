# Module 7: Programming Project - Dessert Shop 5 Console Application

Read all instructions carefully. Not following instructions will result in you not earning the credit you want for the assignment.

**Big Note:** The starting point for Part 5 is the seven files you submitted for Part 4:

- `dessert.py`
    
- `dessertshop.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    

# Objectives

In Part 5, you will learn the following:

- Include a terminal-based user interface in your application
    
- Do input validation
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `Order`
            
        - `DessertItem`
            
        - `Candy`
            
        - `Cookie`
            
        - `IceCream`
            
        - `Sundae`
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main` (update)
            
    - Classes
        
        - `DessertShop` (new)
            

# Problem

In this part of the project, you add a command line user interface to your program. To do this, you will make changes to `dessertshop.py` module.

There should be no changes to the `DessertItem` class and the subclasses.

# Changes to dessertshop module

Add a new class **`DessertShop`** to the module. The `DessertShop` class will have 4 new methods:

- `user_prompt_candy()`
    
- `user_prompt_cookie()`
    
- `user_prompt_icecream()`
    
- `user_prompt_sundae()`
    

Each method should do the following:

1. Prompt user for enough input to create the required line item on the receipt
    
2. Get user input
    
3. Validate the input
    
    - If an input is invalid (e.g., a negative price or quantity), continue prompting the user until a valid value is entered.
        
4. Convert input values to the proper types as-needed
    
5. Create an object of the proper type
    
6. Return the newly created object to the caller
    

## `main()` Code to Copy and Use

We give you code that runs the main loop in the provided file `ui.py`.

You should be able to cut and paste it into your own main function in your `dessertshop.py` as-is.

At the end of the `main` function, print the receipt to the console exactly as you implemented it in Part 4.

# Test Cases

You do not need to create any new pytest test cases for Part 5. However, make sure to upload your existing test cases and re-run them to ensure they still pass.

# Key Program Requirements

1. Dessert Shop 5 extends the functionality of Dessert Shop 4.
    
2. A terminal-based user interface has been added to your Dessert Shop program.
    
3. Output should look similar to the sample run.
    
4. Submit the following 7 files in your workspace:
    

- `dessert.py`
    
- `dessertshop.py`
    
- `test_dessert.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    

Only `dessertshop.py` should have changed in Part 5 unless you needed to correct other issues.

# Sample Run

1: Candy  
2: Cookie  
3: Ice Cream  
4: Sundae  
What would you like to add to the order? (1-4, Enter for done): 1  
​Enter name of candy: Candy Corn  
Enter weight (lbs): 5  
Enter price per pound: 4.99  
  
1: Candy  
2: Cookie  
3: Ice Cream  
4: Sundae  
  
What would you like to add to the order? (1-4, Enter for done): 3  
​Enter the type of ice cream: Pistachio  
Enter the number of scoops: 2  
Enter the price per scoop: 0.79  
  
1: Candy  
2: Cookie  
3: Ice Cream  
4: Sundae  
  
​What would you like to add to the order? (1-4, Enter for done): 4  
Enter the type of ice cream: Vanilla  
Enter the number of scoops: 3  
Enter the price per scoop: 0.69  
Enter the topping: Hot Fudge  
Enter the price for the topping: 1.29  
  
1: Candy  
2: Cookie  
3: Ice Cream  
4: Sundae  
  
What would you like to add to the order? (1-4, Enter for done):

## Example Receipt

The receipt shown does not exactly match the scenario above, but shows you what would be printed to the console if these are the items you ordered.

```
Name                         Cost          Tax
_________________________    __________    __________
Candy Corn                   $0.38         $0.03
Gummy Bears                  $0.09         $0.01
Chocolate Chip               $2.0          $0.14
Pistachio                    $1.58         $0.11
Vanilla                      $3.36         $0.24
Oatmeal Raisin               $0.57         $0.04
____________                 __________    __________
Order Subtotals              $7.98         $0.57
Order Total                                $8.55
Total Items in the order:                  6
```

# Grading

This project is manually graded. Use the following rubric.

| Criteria                                                  | Mastery (100%)                                                                                                                                                                                              | Developing (75%)                                                                                                                     | Beginning (50%)                                                                      |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **Implementation of `DessertShop` class and its methods** | All the methods (`user_prompt_candy`, `user_prompt_cookie`, `user_prompt_icecream`, `user_prompt_sundae`) have been implemented correctly in the `DessertShop` class according to the problem requirements. | Most of the methods have been implemented correctly, but there may be one or two methods missing or incorrect.                       | Few or none of the methods in the DessertShop class have been implemented correctly. |
| **User input validation**                                 | All user inputs are validated properly for every method in `DessertShop` class.                                                                                                                             | Some of the user inputs are validated properly, but there are issues with others.                                                    | Few or none of the user inputs are validated properly.                               |
| **Object creation based on user input**                   | For each method in the `DessertShop` class, objects are correctly created based on user input and returned to the caller.                                                                                   | For most methods, objects are correctly created based on user input, but there may be one or two methods where this is not the case. | Few or none of the methods correctly create and return objects based on user input.  |
| **Program output**                                        | Program output matches exactly with the sample output provided in the problem.                                                                                                                              | Program output mostly matches the sample output, with minor discrepancies.                                                           | Program output does not match the sample output or is missing entirely.              |
| **Integration of Part 4 Code**                            | Part 5 correctly builds on Part 4, reusing and integrating all relevant components from the previous part.                                                                                                  | Part 5 includes most necessary components from Part 4, though a few may be missing or altered.                                       | Key components from Part 4 are missing or improperly integrated.                     |
| **Regression testing (Existing test cases still pass)**   | All existing test cases pass without any modifications required.                                                                                                                                            | Some existing test cases pass without modifications, but others fail or require modifications.                                       | Most or all existing test cases fail or require modifications.                       |

Students should aim for the Mastery level in all categories to ensure they have met all the requirements of the problem. Lower levels represent areas where additional learning and practice may be necessary. As with previous Parts, the overall score is the average of the individual criteria scores.

# What to Submit

Upload the following files to Canvas:

- `dessert.py`
    
- `dessertshop.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`