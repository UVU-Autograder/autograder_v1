# Module 12: Programming Project - Dessert Shop 10 Combine Like Items

Read the instructions carefully. Not following the instructions will result in not getting the credit you want for the assignment.

Make sure your output matches the sample run.

**Big Note:** The starting point for Part 10 is the 10 files you submitted for Part 9:

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

- Implement a user-defined Protocol without explicitly inheriting from the protocol class.
    
- Use `isinstance()` to determine if an object belongs to a class.
    
- Use `issubclass()` to determine if one class is a subclass of another class.
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `Order` (update)
            
        - `Candy` (update)
            
        - `Cookie` (update)
            
        - `IceCream`
            
        - `Sundae`
            
        - `DessertItem`
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main`
            
    - Classes
        
        - `DessertShop`
            
- Module name: `packaging`
    
- Module name: `payment`
    
- Module name: `combine` (new)
    
    - Protocol/Interface: `Combinable`
        

# Problem

Suppose you want to add functionality to your Dessert Shop application to combine items in an order that seem to be the same. For example, suppose the order contains two (2) items of Gummy Bears that both cost the same amount, $0.25/lb, but one if for 0.5 lbs and the other is for 1.25 lbs. It makes sense to combine those into 1 item like so: `Gummy Bears: 1.75 lbs @ $0.25/lb`

This would only make sense if both the item name and price per pound were the same. A store may sell one kind of Gummy Bear (blue) at _$0.35/lb_ and another kind of Gummy Bear (green) at _$0.25/lb_. These would be different items and should not be combined.

Only identical Cookie items or identical Candy items can be combined. Trying to package two Ice Cream Sundaes into a single plastic boat wouldn’t work, for example.

It is tempting to implement checks for combining by redefining `==` on combinable DessertItem objects, but this is not a good design idea:

1. We already defined all relational operators in Part 9 to do something else, including `==`.
    
2. The idea of combining to “same” or “similar” items, there’s no concept of ordering, less than, greater than, or sorting, so it would not make sense to try to define that concept that way.
    

# Combinable Protocol

You will define this protocol class in the file `combine.py`.

- Define the protocol class `Combinable`
    
- Decorate the protocol class with `@runtime_checkable`.
    
- Define predicate method `can_combine(self, other: "Combinable")->bool`. It has no body.
    
- Define method `combine(self, other: "Combinable") -> "Combinable"`. It has no body.
    
- A precondition of calling combine successfully is that `can_combine()` would return `True` for the two items.
    

The `Combinable` Protocol would be called a pure Interface in other languages. It specifies methods, but no default implementations. In some places you see the type “Combinable” in quotes. This is necessary when you need to use the type being defined within its definition.

# Changes to Candy class

Implement the Combinable protocol but **do not** not use inheritance.

- can_combine(self, other:"Candy") -> bool
    
    - return `True`only if `other` object meets the following conditions:
        
        - It is an instance of Candy.
            
        - It has the same name as self.
            
        - It has the same price per pound as self.
            
    - otherwise `False`
        
- combine(self, other: "Candy") -> "Candy"
    
    - If `other` is not an instance of `Candy`, raise a `TypeError`.
        
    - Add the weight of other to the weight of self destructively
        
    - Return modified `self`
        

# Changes to Cookie class

Implement the Combinable protocol, but **do not** use inheritance.

- can_combine(self, other:"Cookie") -> bool
    
    - Return `True` only if `other` object meets the following conditions:
        
        - It is an instance of Cookie.
            
        - It has the same name as self.
            
        - It has the same price per dozen as self.
            
    - Otherwise `False`
        
- combine(self, other: "Cookie") -> "Cookie"
    
    - If `other` is not an instance of `Cookie`, raise a `TypeError`.
        
    - Add the quantity of other to the quantity of self destructively
        
    - Return modified `self`
        

# Changes to Order class

- `add()` method Python offers several ways to search a collection or list of items and potentially combine them.
    
    One way is to add the following **mutually-exclusive checks** to Order’s `add()` method:
    

1. If the new item is not `Combinable` or `can_combine()` returns False for all items in the order:
    
    - Add the new item to the order
        
2. If the new item is `Combinable`:
    
    - For each item in the order, if the item is `Combinable` and can be combined with the new item, merge the new item with the existing one in the order.
        

# Test Cases

Add additional test cases to `test_candy.py` and `test_cookie.py` to validate the functionality of the `Combinable` interface.

## New Candy Tests

- Add a test for `can_combine()` to verify it correctly returns True when both items are candies with the same name and price per pound.
    
- Add a test for `can_combine()` to verify it correctly returns False when both items are candies with the same name but different prices per pound.
    
- Add a test for `can_combine()` to verify it correctly returns False when both items are candies with different names but the same price per pound.
    
- Add a test for `can_combine()` to verify it correctly returns False when the other item is not a `Candy`.
    
- Add a test for `combine()` to verify it correctly combines two `Candy` items when they can be combined.
    
- Add a test for `combine()` to verify it correctly raises `TypeError` when the other item is not a `Candy`.
    

## New Cookie Tests

- Add a test for `can_combine()` that should correctly return True if both are cookies with the same name and price per dozen .
    
- Add a test for `can_combine()` to verify it correctly returns False when both items are cookies with the same name but different prices per dozen.
    
- Add a test for `can_combine()` to verify it correctly returns False when both items are cookies with different names but the same price per dozen.
    
- Add a test for `can_combine()` that should correctly return False if the other item is not a Cookie.
    
- Add a test for `combine()` that should correctly combine two Cookie items when they can be combined.
    
- Add a test for `combine()` to verify it correctly raises `TypeError` when the other item is not a `Cookie`.
    

# Key Program Requirements

1. Dessert Shop 10 builds upon the features of Dessert Shop 9.
    
2. Create the `Combinable` protocol in file `combinable.py`.
    
    - Decorate the protocol class with `@runtime_checkable`.
        
    - Define two methods `can_combine` and `combine` without implementations
        
3. Implement the `Combinable` protocol in the `Candy` and `Cookie` classes.
    
4. Update `add()` method in `Order` class to allow like items to be combined.
    
5. pytest test cases have been created to test True and False cases for `can_combine`.
    
6. pytest test cases have been created to test cases where two items can be combined and cases where two items cannot be combined.
    
7. The receipt shows orders with items combined as in the example run.
    
8. Your workspace contains all the files from Part 9 and:
    
    - new file `combine.py`
        
    
    - the following are modified:
        
        - `dessert.py`
            
            - `test_candy.py`
                
            - `test_cookie.py`
                

# Example Run

In this scenario, we show an abbreviated interaction with the menu because that did not change. We also show a receipt with **two** entries for Gummy Bears and **two** entries for Chocolate Chip because the unit price is different.

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
-    0.5 lbs. @ $0.35/lb:                    $0.17       [Tax: $0.01]  
Candy Corn (Bag)  
-    1.5 lbs. @ $0.25/lb:                    $0.38       [Tax: $0.03]  
Gummy Bears (Bag)  
-    1.5 lbs. @ $0.25/lb:                    $0.38       [Tax: $0.03]  
Chocolate Chip Cookies (Box)  
-    1 cookies. @ $5.99/dozen:               $0.5        [Tax: $0.04]  
Pistachio Ice Cream (Bowl)  
-    2 scoops. @ $0.79/scoop:                $1.58       [Tax: $0.11]  
Chocolate Chip Macadamia Cookies (Box)  
-    5 cookies. @ $4.99/dozen:               $2.08       [Tax: $0.15]  
Hot Fudge Vanilla Sundae (Boat)  
-    3 scoops. @ $0.69/scoop  
-    Hot Fudge topping @ $1.29:              $3.36       [Tax: $0.24]  
Chocolate Chip Cookies (Box)  
-    11 cookies. @ $3.99/dozen:              $3.66       [Tax: $0.27]  
Sprinkles Mint Chocolate Chip Sundae (Boat)  
-    4 scoops. @ $0.89/scoop  
-    Sprinkles topping @ $0.79:              $4.35       [Tax: $0.32]  
----------                                   ----------  ----------  
Total number of items in order:              9  
Order Subtotals:                             $16.46      [Tax: $1.2]  
Order Total:                                             $17.66  
--------------------  
Paid with CARD  
-------------------------------------------  ----------  ------------

# Grading

This project is manually graded. Use the following rubric.

| Criteria                                        | Mastery (100%)                                                                                     | Developing (85%)                                                                                        | Beginning (70%)                                                                           | Low (50%)                                                                                                  |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Implementation of the `Combinable` Protocol** | - Properly defined in `combine.py` - All required methods present and correct                      | - Defined in `combine.py` - One method is missing or improperly implemented                             | `combine.py` is present but improperly defined                                            | `combine.py` missing or no reference to Combinable                                                         |
| **`Candy` and `Cookie` Class Implementation**   | - Implements `Combinable` without inheritance - All methods function correctly                     | - Implements `Combinable` - One or more methods have issues                                             | Only Candy or Cookie implements `Combinable`                                              | Neither Candy nor Cookie implements `Combinable`                                                           |
| **`Order` Class Changes**                       | - Proper checks and full functionality in `add()`                                                  | Some modifications but minor issues present                                                             | -Minimal modifications in `add()`                                                         | - No changes related to Combinable in `add()`                                                              |
| **Test Cases**                                  | All test cases created and correct                                                                 | Most test scenarios covered but one or more missing or incorrect                                        | Few test scenarios covered                                                                | No or minimal test cases related to Combinable                                                             |
| **Integration of Part 9 Code**                  | Part 10 correctly builds on Part 9, reusing and integrating all relevant components appropriately. | Part 10 includes most necessary components from Part 9, with only minor issues in reuse or integration. | Key components from Part 9 are missing, only partially reused, or incorrectly integrated. | Part 10 shows minimal or incorrect integration with Part 9; many essential elements are missing or broken. |

Students should aim for the Mastery level in all categories to ensure they have fully understood and implemented the concepts covered in the project. The overall project score is the average of the individual criteria scores.

# What to Submit

Upload the following files to Canvas:

- `dessert.py`
    
- `dessertshop.py`
    
- `packaging.py`
    
- `payment.py`
    
- `combine.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    
- `test_order.py`