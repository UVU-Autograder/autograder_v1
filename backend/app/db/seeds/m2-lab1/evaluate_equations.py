"""Module 2 Lab 1: Evaluate Equations with Different Parentheses Scopes."""

# Equation 1: Addition and multiplication
# Parentheses alter the order: multiplication standard precedence is changed when grouping addition
eq1_case1 = 2 + (3 * 4)  # Evaluates to 14
eq1_case2 = (2 + 3) * 4  # Evaluates to 20
print("Equation 1: 2 + 3 * 4")
print(f"Case 1: 2 + (3 * 4) = {eq1_case1}")
print(f"Case 2: (2 + 3) * 4 = {eq1_case2}")

# Equation 2: Subtraction and division
# Division takes higher precedence than subtraction unless grouped by parentheses
eq2_case1 = 10 - (4 / 2)  # Evaluates to 8.0
eq2_case2 = (10 - 4) / 2  # Evaluates to 3.0
print("\nEquation 2: 10 - 4 / 2")
print(f"Case 1: 10 - (4 / 2) = {eq2_case1}")
print(f"Case 2: (10 - 4) / 2 = {eq2_case2}")

# Equation 3: Multiplication and addition
# Parentheses determine whether addition occurs before multiplication
eq3_case1 = (5 * 2) + 8  # Evaluates to 18
eq3_case2 = 5 * (2 + 8)  # Evaluates to 50
print("\nEquation 3: 5 * 2 + 8")
print(f"Case 1: (5 * 2) + 8 = {eq3_case1}")
print(f"Case 2: 5 * (2 + 8) = {eq3_case2}")
