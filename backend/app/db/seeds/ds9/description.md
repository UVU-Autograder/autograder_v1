# Module 11: Programming Project - Dessert Shop 9 Sort Receipt Items

Read the instructions carefully. Not following the instructions will result in not getting credit for the assignment.

Make sure your output matches the example run.

**Big Note:** The starting point for Part 9 is the 10 files you submitted for Part 8:

- `dessert.py`
    
- `dessertshop.py`
    
- `packaging.py`
    
- `payment.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    
- `test_order.py`
    

# Objectives

In Part 9, you will learn how to do the following:

- Implement an informal, implicit protocol to make dessert items comparable
    
- Sort a list of user-defined objects using the attributes of a class
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `Order` (update)
            
        - `Candy`
            
        - `Cookie`
            
        - `IceCream`
            
        - `Sundae`
            
        - `DessertItem` (update)
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main` (update)
            
    - Classes
        
        - `DessertShop`
            
- Module name: `packaging`
    
- Module name: `payment`
    

# Problem

Suppose you want to add functionality to your Dessert Shop application to sort the items on your receipt so that the least expensive is at the top and the most expensive is at the bottom. You will need to sort your order (conceptually a list of items) based on a pre-defined data member (attribute) of your class.

For Part 8 we will only consider the price, not other ways we could arrange items.

# Changes to DessertItem class

- Implement `__eq__`, `__ne__`, `__lt__`, `__gt__`,`__ge__`, `__le__` operators using the price.
    

# Changes to Order class

Add method:

- `sort():` Sort the items by price in ascending order.
    

Keep in mind that an Order is **not** a list–it is an object of type **Order** that has an attribute that is a list. We can access that attribute as-needed.

# Changes to main

Sort the dessert items in an Order

- after all items are added, but
    
- before it is printed
    

## Test Cases

Add pytest test cases to `test_dessert.py` that test all of the relational operators =,<,≤,>,≥=,<,≤,>,≥. Test all operators once.

Add one pytest test case to `test_order.py` that tests the sort method.

# Key Program Requirements

1. Dessert Shop 9 extends the functionality of Dessert Shop 8.
    
2. All relational operators are implemented in `DessertItem`.
    
3. All relational operators are tested at least once.
    
4. The receipt shows items sorted by price in ascending order.
    
5. Files modified:
    
    - `dessert.py`
        
    
    - `dessertshop.py`
        
    
    - `test_order.py`
        
    
    - `test_dessert.py`
        

## Example Run

1: Candy  
2: Cookie  
3: Ice Cream  
4: Sunday  
What would you like to add to the order? (1-4, Enter for done): 2  
​  
Enter the type of cookie: Chocolate Chip Macadamia  
Enter the quantity purchased: 5  
Enter the price per dozen: 4.99  
  
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
  
1: Candy  
2: Cookie  
3: Ice Cream  
4: Sunday  
What would you like to add to the order? (1-4, Enter for done):  
​  
1:CASH  
2:CARD  
3:PHONE  
Enter payment method): 2

# Example Receipt

-------------------------------------------  ----------  ------------  
Name                                         Cost        Tax  
----------                                   ----------  ----------  
Gummy Bears (Bag)  
-    0.25 lbs. @ $0.35/lb:                   $0.09       [Tax: $0.01]  
Candy Corn (Bag)  
-    1.5 lbs. @ $0.25/lb:                    $0.38       [Tax: $0.03]  
Pistachio Ice Cream (Bowl)  
-    2 scoops. @ $0.79/scoop:                $1.58       [Tax: $0.11]  
Chocolate Chip Cookies (Box)  
-    6 cookies. @ $3.99/dozen:               $2.0        [Tax: $0.14]  
Chocolate Chip Macadamia Cookies (Box)  
-    5 cookies. @ $4.99/dozen:               $2.08       [Tax: $0.15]  
Hot Fudge Vanilla Sundae (Boat)  
-    3 scoops. @ $0.69/scoop  
-    Hot Fudge topping @ $1.29:              $3.36       [Tax: $0.24]  
Sprinkles Mint Chocolate Chip Sundae (Boat)  
-    4 scoops. @ $0.89/scoop  
-    Sprinkles topping @ $0.79:              $4.35       [Tax: $0.32]  
----------                                   ----------  ----------  
Total number of items in order:              7  
Order Subtotals:                             $13.84      [Tax: $1.0]  
Order Total:                                             $14.84  
--------------------  
Paid with CARD  
-------------------------------------------  ----------  ------------

# Grading

This project is manually graded. Use the following rubric.

| Criteria                                                     | Mastery (100%)                                                                                                | Developing (85%)                                                                                                                    | Beginning (70%)                                                                                                      | Low (50%)                                                                                                                           |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Implementation of relational operators and `sort` method** | All relational operators and the `sort` method are implemented.                                               | Relational operators and the `sort` method are implemented but with minor errors in methods or error handling.                      | Relational operators and the `sort` method are implemented but with significant errors in methods or error handling. | Relational operators and the `sort` method are either not implemented or incorrectly implemented.                                   |
| **Test Cases**                                               | All required test cases are implemented correctly and pass. Each relational operator is tested at least once. | Most required test cases are implemented and pass, but there may be a few missing or failing tests.                                 | Some required test cases are implemented and pass, but there are significant gaps in test coverage.                  | Few or no required test cases are implemented, or most tests fail.                                                                  |
| **Receipt Output**                                           | The receipt correctly includes information for each item. Items appear in ascending order by cost.            | The receipt includes information for most items, but there may be a few errors or omissions. Some items may not be in sorted order. | The receipt includes information for some items, but there are significant errors or omissions.                      | The receipt does not include correct information for the items or has serious errors. Sorting was not implemented, or mostly fails. |
| **Integration of Part 8 Code**                               | Part 9 correctly builds on Part 8, reusing and integrating all relevant components appropriately.             | Part 9 includes most necessary components from Part 8, with only minor issues in reuse or integration.                              | Key components from Part 8 are missing, only partially reused, or incorrectly integrated.                            | Part 9 shows minimal or incorrect integration with Part 8; many essential elements are missing or broken.                           |

Students should aim for the Mastery level in all categories to ensure they have fully understood and implemented the concepts covered in the project. The overall project score is the average of the individual criteria scores.

# What to Submit

Upload the following files to Canvas:

- `dessert.py`
    
- `dessertshop.py`
    
- `packaging.py`
    
- `payment.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    
- `test_order.py`