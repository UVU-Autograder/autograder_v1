# Module 8: Programming Project - Dessert Shop 6 Overriding Methods

Read all instructions carefully. Not following instructions will result in you not earning the credit you want for the assignment.

**Big Note:** The starting point for Part 6 is the seven files you submitted for Part 5:

- `dessert.py`
    
- `dessertshop.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`
    

# Objectives

In Part 6, you will learn the following:

- Override `__str__` magic method to customize the printable version of an object.
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `Order` (update)
            
        - `DessertItem`
            
        - `Candy` (update)
            
        - `Cookie` (update)
            
        - `IceCream` (update)
            
        - `Sundae`(update)
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main` (update)
            
    - Classes
        
        - `DessertShop`
            

# Problem

In this part of the project, you will override the default magic `__str__` method in all classes to enable printing a receipt using the built-in `print` function. You have implemented `__str__` method in a previous project, but now we present it in the context of overriding the default implementation.

# Changes to the Concrete Subclasses of DessertItem

Add `__str__` method to `Candy`, `Cookie`, `IceCream`, `Sundae` classes.

Do **not** print in this method. Per the Python docs, this method returns a string to the caller.

The string representation for each itme should include item name, quantity, price per unit, cost, and tax.For `Sundae`, include an additional line with details about the topping in a comma-separated format.

Examples:

**Candy**

For `Candy('Candy Corn', 1.5, 0.25)`:

Candy Corn  
-    1.5 lbs. @ $0.25/lb:, $0.38, [Tax: $0.03]

**Cookie**

For `Cookie('Chocolate Chip Macadamia', 5, 4.99)`:

Chocolate Chip Macadamia Cookies  
-    5 cookies. @ $4.99/dozen:, $2.08, [Tax: $0.15]

**Ice Cream**

For `IceCream('Pistachio', 2, 0.79)`:

Pistachio Ice Cream  
-    2 scoops. @ $0.79/scoop:, $1.58, [Tax: $0.11]

**Sundae**

For `Sundae('Vanilla', 3, 0.69, 'Hot Fudge', 1.29)`:

Hot Fudge Vanilla Sundae  
-    3 scoops. @ $0.69/scoop  
-    Hot Fudge topping @ $1.29:, $3.36, [Tax: $0.24]

As always, I suggest using **f-strings** to build these strings. We format the Item strings this way because it makes the string form easier to process programmatically, while still being human-readable.

# Changes to `Order` Class

- Add `__str__` method to `Order` class.
    

When you print an order to the terminal, it does not need to be in nice columns, just print comma-separated values for each line.

- Add `to_list()` method to `Order` class
    
    - This method converts the string representation of an order into a 2D list
        
        - Splits the string by new line character
            
        - Then splits each string in the list by the comma
            
    - Returns the resulting list to the caller
        

# Changes to dessertshop module

Replace your `main` function with the following code:

def main():  
    shop = DessertShop()   
    order = Order()  
      
    # order.add(Candy('Candy Corn', 1.5, 0.25))  
    # order.add(Candy('Gummy Bears', 0.25, 0.35))  
    # order.add(Cookie('Chocolate Chip', 6, 3.99))  
    # order.add(IceCream('Pistachio', 2, 0.79))  
    # order.add(Sundae('Vanilla', 3, 0.69, 'Hot Fudge', 1.29))  
    # order.add(Cookie('Oatmeal Raisin', 2, 3.45))  
      
    done: bool = False  
    # build the prompt string once  
    prompt = '\n'.join([ '\n',  
            '1: Candy',  
            '2: Cookie',              
            '3: Ice Cream',  
            '4: Sundae',  
            '\nWhat would you like to add to the order? (1-4, Enter for done): '  
      ])  
​  
    while not done:  
      choice = input(prompt)  
      match choice:  
        case '':  
          done = True  
        case '1':              
          item = shop.user_prompt_candy()  
          order.add(item)  
          print(f'{item.name} has been added to your order.')  
        case '2':              
          item = shop.user_prompt_cookie()  
          order.add(item)  
          print(f'{item.name} has been added to your order.')  
        case '3':              
          item = shop.user_prompt_icecream()  
          order.add(item)  
          print(f'{item.name} has been added to your order.')  
        case '4':              
          item = shop.user_prompt_sundae()  
          order.add(item)  
          print(f'{item.name} has been added to your order.')  
        case _:              
          print('Invalid response:  Please enter a choice from the menu (1-4) or Enter')  
    print()  
      
    # Add your code below here to print the receipt as the last thing in main()  
    # Make sure that the output format matches the provided sample run  
​  
    print(tabulate(order.to_list(), tablefmt="fsql"))

**Note:**

The following line should be the only print statement used for generating the receipt in your `main` function:

print(tabulate(order.to_list(), tablefmt="fsql"))

# Test Cases

There are no new automated test cases to add. Upload and run your existing automated test cases to make sure they still pass. Then verify by manual inspection that this new version with overridden string methods is correct.

# Key Program Requirements

1. Dessert Shop 6 extends the functionality of Dessert Shop 5.
    
2. No printing to the console occurs in any class other than `DessertShop` or any function other than `main()`.
    
3. In the `main()` function, use a single line to print the entire order.
    
4. `__str__` methods should be implemented in the `Candy`, `Cookie`, `IceCream`, `Sundae`, and `Order` classes. Each method must return a properly formatted string that represents the state of the corresponding object.
    
5. `to_list()` method converts the string respresentation of an order to a 2D list and returns that list.
    
6. Submit the following 7 files in your workspace:
    

- - `dessert.py`
        
    - `dessertshop.py`
        
    - `test_dessert.py`
        
    - `test_candy.py`
        
    - `test_cookie.py`
        
    - `test_icecream.py`
        
    - `test_sundae.py`
        

# Sample Run

  
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

## Example Receipt

The receipt shown does not exactly match the scenario above, but shows you what would be printed to the console if these are the items you ordered.

  
-------------------------------  ----------  ------------  
Name                             Cost        Tax  
----------                       ----------  ----------  
Candy Corn  
-    1.5 lbs. @ $0.25/lb:        $0.38       [Tax: $0.03]  
Gummy Bears  
-    0.25 lbs. @ $0.35/lb:       $0.09       [Tax: $0.01]  
Chocolate Chip Cookies  
-    6 cookies. @ $3.99/dozen:   $2.0        [Tax: $0.14]  
Pistachio Ice Cream  
-    2 scoops. @ $0.79/scoop:    $1.58       [Tax: $0.11]  
Hot Fudge Vanilla Sundae  
-    3 scoops. @ $0.69/scoop  
-    Hot Fudge topping @ $1.29:  $3.36       [Tax: $0.24]  
Oatmeal Raisin Cookies  
-    2 cookies. @ $3.45/dozen:   $0.57       [Tax: $0.04]  
----------                       ----------  ----------  
Total number of items in order:  6  
Order Subtotals:                 $7.98       [Tax: $0.57]  
Order Total:                                 $8.55  
-------------------------------  ----------  ------------

# Grading

This project is manually graded. Use the following rubric for grading.

| Criteria                                                                           | Mastery (100%)                                                                                                                                                                                 | Developing (75%)                                                                                                                                                    | Beginning (50%)                                                                                                        |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Overriding the `__str__` method and adding `to_list()` method to `Order` class** | The `__str__` method is correctly overridden in all required classes (`Candy`, `Cookie`, `IceCream`, `Sundae`, `Order`). The `to_list`() method is correctly implemented in the `Order` class. | The `__str__` method is overridden in most required classes, but some may be missing or incorrect. The `to_list()` method is present but not correctly implemented. | Few or none of the required classes have the `__str__` method correctly overridden. The `to_list()` method is missing. |
| **Formatting of the returned string in the `__str__` method**                      | All overridden `__str__` methods return a string formatted according to the specifications for each class.                                                                                     | Most overridden `__str__` methods return a string formatted correctly, but there may be some discrepancies.                                                         | Few or none of the overridden `__str__` methods return a string formatted correctly.                                   |
| **Program output**                                                                 | Program output matches exactly with the sample output provided in the problem.                                                                                                                 | Program output mostly matches the sample output, with minor discrepancies.                                                                                          | Program output does not match the sample output or is missing entirely.                                                |
| **No printing to the console outside of `DessertShop` and `main()`**               | No console printing occurs outside of the `DessertShop` class or `main()` function.                                                                                                            | Most console printing is limited to the `DessertShop` class and `main()`, but there may be some instances of printing in other locations.                           | Console printing occurs outside of the `DessertShop` class or `main()` function.                                       |
| **Integration of Part 5 Code**                                                     | Part 6 correctly builds on Part 5, reusing and integrating all relevant components from the previous part.                                                                                     | Part 6 includes most necessary components from Part 5, though a few may be missing or altered.                                                                      | Key components from Part 5 are missing or improperly integrated.                                                       |
| **Regression testing (Existing test cases still pass)**                            | All existing test cases run and pass with no modifications required.                                                                                                                           | Most existing test cases run and pass without modifications, but some may fail or require changes.                                                                  | Few or none of the existing test cases run and pass without modifications.                                             |

Students should aim for the Mastery level in all categories to ensure they have met all the requirements of the problem. Lower levels represent areas where additional learning and practice may be necessary. As with prior Parts, the overall score is the average of the individual criteria scores.

# What to Submit

Upload the following files to Canvas:

- `dessert.py`
    
- `dessertshop.py`
    
- `test_candy.py`
    
- `test_cookie.py`
    
- `test_dessert.py`
    
- `test_icecream.py`
    
- `test_sundae.py`