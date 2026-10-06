# Module 3: Lab 5 - Operator Overloading

# Lab 5: Operator Overloading

In real-world financial applications, using floating-point numbers to represent money is not a good idea. This is because `float` types can introduce precision errors during calculations.

For example:

print(0.1 + 0.2)

You might be surprised to see that the result is **not exactly** 0.3.

This happens because binary floating-point representation cannot precisely store many decimal values. Even small rounding errors can become significant in financial applications.

In this lab, we will represent money using integers by separating dollars and cents. Your task is to update the `Money` class and overload several operators to make `Money` objects behave like numeric types.

## Objectives

- Represent money using dollars and cents as integers
    
- Overload the following operators for the `Money` class:
    
    - `+` (addition)
        
    - `*` (scalar multiplication)
        
    - `==` (equality)
        

## Starter Code

class Money:  
    def __init__(self, dollars, cents):  
        self.dollars = dollars  
        self.cents = cents  
        self.normalize()  
​  
    def normalize(self):  
        if self.cents >= 100:  
            self.dollars += self.cents // 100  
            self.cents = self.cents % 100  
​  
    def __str__(self):  
        return f"${self.dollars}.{self.cents:02d}"  
​  
def main():  
    m1 = Money(3, 50)  
    m2 = Money(2, 75)  
​  
    print("m1:", m1)  
    print("m2:", m2)  
​  
if __name__ == "__main__":  
    main()

## Part 1 – Overload `+` Operator (30 points)

Overload the `+` operator so that two `Money` objects can be added using `+`.

m3 = m1 + m2  
print("m3:", m3)   # Expected: $6.25

## Part 2 – Overload `*` Operator (30 points)

Overload the `*` operator so that a `Money` object can be multiplied by an integer, from either direction.

m4 = m1 * 2  
m5 = 3 * m2  
print("m4:", m4)   # Expected: $7.00  
print("m5:", m5)   # Expected: $8.25

## Part 3 – Overload `==` Operator (30 points)

Overload the `==` operator so that two `Money` objects are equal if both the dollars and cents match.

print(m1 == Money(2, 150))  # Expected: True  
print(m1 == Money(3, 49))   # Expected: False

## Part 4 – `main()` Function (10 points)

In your `main()` function, write code that demonstrates your overloaded operators work as expected.

## What to Submit

Upload `money.py` to Canvas.