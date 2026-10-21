"""Module 2 Lab 2: Compute Areas of Geometric Shapes."""

import math

# Circle Area calculation
radius = float(input("Enter the radius: "))
circle_area = math.pi * (radius ** 2)
print(f"The area of the circle with radius {radius} is {circle_area:.4f}")

# Rectangle Area calculation
width = float(input("Enter the width: "))
height = float(input("Enter the height: "))
rectangle_area = width * height
print(f"The area of the rectangle {width:.0f} x {height:.0f} is {rectangle_area:.4f}")

# Triangle Area calculation
base = float(input("Enter the base: "))
triangle_height = float(input("Enter the height: "))
triangle_area = (base * triangle_height) / 2
print(f"The area of the triangle with base {base:.0f} and height {triangle_height:.0f} is {triangle_area:.4f}")
