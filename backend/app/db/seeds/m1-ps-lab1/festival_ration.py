"""Module 1 PS Lab 1: Festival Ration Preparation."""

# Collect colonist count and total supplies
colonists: int = int(input("Enter the number of colonists: "))
total_supplies: int = int(input("Enter the total food units available: "))

# Calculate ration allocation and remaining stockpile
ration_per_colonist: int = 4
ration_allocation: int = ration_per_colonist * colonists
remaining_stockpile: int = total_supplies - ration_allocation

# Display the calculated outputs
print(f"Original supply: {total_supplies}")
print(f"Ration allocation (4 units per colonist): {ration_allocation}")
print(f"Festival stockpile remaining: {remaining_stockpile}")
