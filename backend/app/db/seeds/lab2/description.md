# Module 2: Lab 2 - Creating a Bank Account Class

Objectives

In this lab, you will:

- Define a Python class
    
- Use default values for attributes
    
- Add a string representation method using `__str__()`
    
- Manually test your class from another file
    

## Instructions

### Part 1 – Define the `Account` class (40 points)

Create a class named `Account` with the following attributes:

- `owner`: the name of the account holder (default: `""`)
    
- `balance`: the account balance (default: `0.0`)
    

> 💡 **Note:** In a real banking system, each account typically has a unique ID. For this lab, we’ll assume the `owner` is unique to keep things simple.

Implement an `__init__` method to initialize these attributes.

Save the `Account` class in a file named `account.py`.

### Part 2 – Add a string representation method (30 points)

Add a method called `__str__()` to your `Account` class. This method defines how the object should appear when printed.

For example, if you create an account like this:

account = Account("Alice", 100)  
print(account)

It should display:

Owner: Alice, Balance: $100.00

### Part 3 – Manually test your class from another file (30 points)

Create a separate Python file called `demo.py` to manually test your `Account` class.

In the `demo` module:

1. Import the `Account` class from `account` module
    
2. Create two `Account` objects:
    
    - One with custom values (e.g., owner is `"Alice"`, balance is `$100`)
        
    - One using default values
        
3. Print both accounts to verify that your code works correctly.
    

## What to Submit

Submit the following two files to Canvas:

- `account.py`
    
- `demo.py`