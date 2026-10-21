"""Module 4 Lab 1: UVU Bookstore Discount Calculator."""

# Prompt user for price and buyer type
item_price = float(input("Enter the item price: "))
buyer_type = input("Enter buyer type (\"s\" for student, \"f\" for faculty): ").strip().lower()

# Apply discount conditionally based on buyer type
if buyer_type == "s":
    discount_rate = 0.05
    discount_percent = "5%"
elif buyer_type == "f":
    discount_rate = 0.08
    discount_percent = "8%"
else:
    discount_rate = 0.0
    discount_percent = "0%"

discount_amount = item_price * discount_rate
final_price = item_price - discount_amount

# Display formatted result
print(f"Final price after {discount_percent} discount: ${final_price:.2f}")
