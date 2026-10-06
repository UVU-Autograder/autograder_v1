# Module 6: Programming Project - Dessert Shop 4 Abstraction

Read instructions carefully. Not following instructions will result in not getting the credit you want.

Make sure your output matches the sample run.

**Big Note:** The starting point for Part 4 is the two files you submitted for Part 3: `dessert.py` and `test_dessert.py`.

# Objectives

In Part 4, you will learn the following:

- Create an Abstract Base Class (ABC)
    
- Create abstract methods in a base class and concrete methods in subclasses
    
- Update existing classes to include additional methods
    
- Add new pytest test cases to existing test code
    
- Regression test existing methods through pytest test cases
    
- Print out the receipt to the console
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `Order` (update)
            
        - `DessertItem` (update)
            
        - `Candy` (update)
            
        - `Cookie` (update)
            
        - `IceCream` (update)
            
        - `Sundae` (update)
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main` (update)
            

# Problem

In Part 4, you will add the functionality to calculate the cost of any Dessert Item along with the associated tax. Also you will add the ability in the `Order` class to calculate the cost of all items in the order as well as the associated total tax.

Finally, you will implement the ability to print out the receipt to the console.

To do this, you will make updates to your Dessert Shop system as described below.

## Changes to DessertItem Class

- Make it an **abstract** class
    
- Add attribute `tax_percent`: float with the default value 7.25.
    
- Add a new abstract method, `calculate_cost()`: float
    
- Include a new method `calculate_tax()`: float that calculates and returns the actual tax for the item, rounded to 2 decimal places.
    

## Changes to All Dessert Classes Candy, Cookie, IceCream, Sundae

- Add a method `calculate_cost()` that overrides the superclass method and returns the correct cost for the item, rounded to 2 decimal places.
    
- Note:
    
    - Convert `cookie_quantity` to dozens before calculating the cost of the cookies.
        
    - The cost of a Sundae is the cost of the ice cream plus the cost of the topping.
        

## Changes to Order Class

- Add a new method, `order_cost()`, that calculates and returns the total cost for all items in the order
    
- Add a new method, `order_tax()`, calculates and returns the total tax for all items in the order
    

## Changes to main()

- Add a loop in the `main()` to generate the list-of-lists required by `tabulate`. Each row in the list should include:
    
    - The **name** of the dessert,
        
    - The **cost** of each item
        
    - The **tax** of the item
        
    
    Values should match what is shown in the example run below.
    
- Add a row for **subtotal** of all the items in the order and the **total tax** for the order as shown in the example.
    
- Add a row for the **total cost** for the order (subtotal + total tax)
    
- Add a row for the **total number of items** in the order as shown in the example
    
- Print the receipt using `tabulate`. You output should match the provided sample run.
    

Example of using `tabulate`:

from tabulate import tabulate  
​  
data = [  
    ["Will", 15],  
    ["Hope", 19],  
    ["Jill", 20],  
]  
​  
​  
print(tabulate(data, headers=["Character", "Age"], tablefmt="fsql"))

# Test Cases

- Modify your DessertItem test cases to use an instance of the Candy class. You have to test an abstract class by testing one of its concrete subclasses.
    
- Add new test cases to DessertItem test code that test the tax_percent attribute
    
- Add new test cases to test method calculate_cost for each respective dessert subclass.
    
- Add new test cases to test superclass method calculate_tax for each respective dessert subclass. Hint: Use the code that created example objects in main() from Part 2 as a source of test cases for each kind of object here.
    

## Sample Run

Your output format and values should match what is here.

```
Name                         Cost          Tax
_________________________    __________    __________
Candy Corn                   $0.38         $0.03
Gummy Bears                  $0.09         $0.01
Chocolate Chip               $2.0          $0.14
Pistachio                    $1.58         $0.11
Vanilla                      $3.36         $0.24
Oatmeal Raisin               $0.57         $0.04
____________                 __________    __________
Order Subtotals              $7.98         $0.57
Order Total                                $8.55
Total Items in the order:                  6
```
# Key Requirements

1. Dessert Shop 4 extends the functionality of Dessert Shop 3.
    
2. Attribute `tax_percent` is in DessertItem class
    
3. Method `calculate_cost` is abstract in DessertItem and concrete in all inheriting subclasses
    
4. Method `calculate_tax` is concrete in DessertItem and is **NOT** overrriden in any inheriting subclasses
    
5. Pytest test cases have been created or modified as described above
    
6. The output should look similar to the sample run shown above
    
7. Your workspace should have the following 7 files:
    
    - `dessert.py`
        
    - `dessertshop.py`
        
    - `test_dessert.py`
        
    - `test_candy.py`
        
    - `test_cookie.py`
        
    - `test_icecream.py`
        
    - `test_sundae.py`
        
    
    This way you don’t end up with one huge test file.
    

# Grading

This project is manually graded. Part of that grade includes running your test cases. Use the following rubric.

Here’s a possible mastery-based grading rubric for this problem:

| Criteria                             | Mastery (100%)                                                                                                     | Approaching Mastery (75%)                                                                                                   | Developing (65%)                                                                                               | Beginning (50%)                                                        |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **`tax_percent` attribute**          | `tax_percent` attribute is correctly implemented in DessertItem class                                              | `tax_percent` attribute is implemented in DessertItem class, but there are some minor errors                                | `tax_percent` attribute is present but not correctly implemented                                               | `tax_percent` attribute is not implemented                             |
| **Abstract `calculate_cost` method** | Correctly implemented as an abstract method in `DessertItem` and correctly overridden in all inheriting subclasses | Correctly implemented as an abstract method in `DessertItem`, but there are some errors in the implementation in subclasses | `calculate_cost` method is present but not correctly implemented as an abstract method or correctly overridden | `calculate_cost` method is not implemented                             |
| **`calculate_tax` method**           | Correctly implemented in `DessertItem` and not overridden in any inheriting subclasses                             | Correctly implemented in `DessertItem`, but there are some minor errors                                                     | `calculate_tax` method is present but not correctly implemented                                                | `calculate_tax` method is not implemented                              |
| **Test cases**                       | All required pytest test cases, including new and old test cases, have been created and all tests pass             | All required pytest test cases, including new and old test cases, have been created but some tests do not pass              | Some required pytest test cases are missing or there are significant errors                                    | No or very few correct pytest test cases                               |
| **Receipt format and values**        | The receipt is printed to the console and matches the example in both format and values                            | The receipt is printed to the console, but there are some errors in the format or values                                    | Some attempt has been made to print out the receipt, but it is significantly incorrect                         | No attempt has been made to print out the receipt                      |
| **Integration of Part 3 Code**       | Part 4 correctly builds on Part 3 and includes all relevant code from the previous assignment.                     | Part 4 includes most of the code from Part 3 with minor omissions.                                                          | Part 4 includes some code from Part 3 but lacks important components.                                          | Part 4 includes very little from Part 3 or the integration is unclear. |
| **Code organization**                | Code is correctly divided into the 7 required files                                                                | Code is divided into files, but not exactly as specified                                                                    | Some attempt has been made to divide the code into files, but there are significant errors                     | Code is not divided into separate files                                |

In this rubric, each criterion is evaluated independently and contributes to the overall score for the assignment.

For example, if a student's code has mastery level "Order Class Structure" (60 points), approaching mastery "Order Class Methods" (45 points), developing "Main Function" (39 points), beginning "Program Output" (30 points), mastery level "Integration of Part 3 Code" (60 points), mastery level "Receipt format and values" (60 points), and approaching mastery "Code Quality" (45 points), the student's total score would be the average of these seven scores.

# What to Submit

Upload the following files to Canvas:

- `dessert.py`
    
- `dessertshop.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`