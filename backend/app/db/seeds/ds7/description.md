# Module 9: Programming Project - Dessert Shop 7 Mixin Interface

Read all instructions carefully. Not following instructions will result in you not earning the credit you want for the assignment.

**Big Note**: The starting point for Part 7 is the seven files you submitted for Part 6:

- `dessert.py`
    
- `dessertshop.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    

# Objectives

In Part 7, you will learn the following:

- Add an inherited property defined by a Protocol class (Interface in other languages)
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `Order`
            
        - `DessertItem` (update)
            
        - `Candy` (update)
            
        - `Cookie` (update)
            
        - `IceCream` (update)
            
        - `Sundae` (update)
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main`
            
    - Classes
        
        - `DessertShop`
            
- Module name: `packaging` (new)
    

# Problem

Suppose you want to add functionality to your Dessert Shop application to identify what type of packaging a dessert item should be placed in. These packaging types will show up on the receipt. Each item will show what type of packaging it will be place in. All items of a similar type will use the same type of packaging.

Because a property like packaging could be used in multiple applications, we put it in its own module and define an explicit type.

To do this, you will add an interface to your Dessert Shop application and update your receipt output as described below.

# Packaging Protocol Class

Define a new Protocol class `Packaging` that has one attribute `packaging` of type `str`. It should be in file `packaging.py`.

In other programming languages like Java, we would define a getter and setter in this interface. But in Python, we’ll just define an attribute and use it directly.

# Changes to DessertItem class

Change the `DessertItem` class to inherit from the new `Packaging` interface. Do not change the constructor signature, because you can create a dessert and add packaging later. Default value is `None`.

# Changes to the Concrete Subclasses of DessertItem

- set the superclass packaging type within the constructor; the default value for each respective type is as follows:
    
    - for Candy: packaging = “Bag”
        
    - for Cookie: packaging = “Box”
        
    - for Ice Cream: packaging = “Bowl”
        
    - for Sundae: packaging = “Boat”
        
- modify the `__str__` magic method to include the packaging type as shown in the sample run
    

# Test Cases

Add automated test cases to test correct packaging for each concrete dessert type in their respective pytest test files.

# Key Program Requirements

1. Dessert Shop 7 extends the functionality of Dessert Shop 6.
    
2. The new Protocol class Packaging has been added to your system.
    
3. Test code has been updated to check for the packaging type.
    
4. The receipt has been updated to show packaging.
    

# Example Run

1: Candy  
2: Cookie  
3: Ice Cream  
4: Sunday  
What would you like to add to the order? (1-4, Enter for done): 2  
​  
Enter the type of cookie: Chocolate Chip Macadamia  
Enter the quantity purchased: 5  
Enter the price per dozen: 4.99  
​  
1: Candy  
2: Cookie  
3: Ice Cream  
4: Sunday  
What would you like to add to the order? (1-4, Enter for done):4  
​  
Enter the type of ice cream: Mint Chocolate Chip  
Enter the number of scoops: 4  
Enter the price per scoop: 0.89  
Enter the kind of topping used: Sprinkles  
Enter the price for the topping: 0.79  
​  
1: Candy  
2: Cookie  
3: Ice Cream  
4: Sunday  
What would you like to add to the order? (1-4, Enter for done):

# Example Receipt

-------------------------------  ----------  ------------  
Name                             Cost        Tax  
----------                       ----------  ----------  
Candy Corn (Bag)  
-    1.5 lbs. @ $0.25/lb:        $0.38       [Tax: $0.03]  
Gummy Bears (Bag)  
-    0.25 lbs. @ $0.35/lb:       $0.09       [Tax: $0.01]  
Chocolate Chip Cookies (Box)  
-    6 cookies. @ $3.99/dozen:   $2.0        [Tax: $0.14]  
Pistachio Ice Cream (Bowl)  
-    2 scoops. @ $0.79/scoop:    $1.58       [Tax: $0.11]  
Hot Fudge Vanilla Sundae (Boat)  
-    3 scoops. @ $0.69/scoop  
-    Hot Fudge topping @ $1.29:  $3.36       [Tax: $0.24]  
Oatmeal Raisin Cookies (Box)  
-    2 cookies. @ $3.45/dozen:   $0.57       [Tax: $0.04]  
----------                       ----------  ----------  
Total number of items in order:  6  
Order Subtotals:                 $7.98       [Tax: $0.57]  
Order Total:                                 $8.55  
-------------------------------  ----------  ------------

# Grading

This project is manually graded. Use the following rubric.

| Criteria                                         | Mastery (100%)                                                                                                                   | Developing (85%)                                                                                                                                | Beginning (70%)                                                                                                                                   | Low (50%)                                                                                                          |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Implementation of `Packaging` Protocol Class** | The `Packaging` Protocol class is correctly implemented with the packaging attribute of type `str`.                              | The `Packaging` Protocol class is implemented but with minor errors in the packaging attribute.                                                 | The `Packaging` Protocol class is partially implemented with significant errors in the packaging attribute.                                       | The `Packaging` Protocol class is either not implemented or incorrectly implemented.                               |
| **Changes to `DessertItem` class**               | The `DessertItem` class correctly inherits from the `Packaging` Protocol class with a default value of `None` for packaging.     | The `DessertItem` class inherits from the `Packaging` Protocol class, but there are minor errors in handling default value or inheritance.      | The `DessertItem` class attempts to inherit from the `Packaging` Protocol class, but with significant errors or omissions.                        | The `DessertItem` class does not inherit from the `Packaging` Protocol class or has serious implementation errors. |
| **Changes to `DessertItem` Subclasses**          | All subclasses correctly set the superclass packaging type within the constructor and modify the `__str__` method appropriately. | Most subclasses correctly set the superclass packaging type within the constructor and modify the `__str__` method, but there are minor errors. | Some subclasses set the superclass packaging type within the constructor and attempt to modify the `__str__` method, but with significant errors. | Few or none of the subclasses correctly implement the required changes.                                            |
| **Test Cases**                                   | All required test cases are implemented correctly and pass.                                                                      | Most required test cases are implemented and pass, but there may be a few missing or failing tests.                                             | Some required test cases are implemented and pass, but there are significant gaps in test coverage.                                               | Few or no required test cases are implemented, or most tests fail.                                                 |
| **Receipt Output**                               | The receipt correctly includes packaging information for each item.                                                              | The receipt includes packaging information for most items, but there may be a few errors or omissions.                                          | The receipt includes packaging information for some items, but there are significant errors or omissions.                                         | The receipt does not include correct packaging information for the items or has serious errors.                    |
| **Use of `Packaging` Protocol Class**            | `Packaging` Protocol class is implemented and used correctly across the system.                                                  | `Packaging` Protocol class is mostly implemented and used correctly, but there are minor errors or omissions.                                   | `Packaging` Protocol class is used in some parts of the system, but there are significant errors or omissions.                                    | `Packaging` Protocol class is either not used or incorrectly used across the system.                               |
| **Integration of Part 6 Code**                   | Part 7 correctly builds on Part 6, reusing and integrating all relevant components appropriately.                                | Part 7 includes most necessary components from Part 6, with only minor issues in reuse or integration.                                          | Key components from Part 6 are missing, only partially reused, or incorrectly integrated.                                                         | Part 7 shows minimal or incorrect integration with Part 6; many essential elements are missing or broken.          |

Students should aim for the Mastery level in all categories to ensure they have fully understood and implemented the concepts covered in the project. Overall score is the average of the individual criteria scores.

# What to Submit

Upload the following files to Canvas:

- `dessert.py`
    
- `dessertshop.py`
    
- `packaging.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`