"""Module 2 PS Lab 1: Festival Resource Distribution - Percent Allocations."""

# Collect input values
colonists = int(input("Enter the number of colonists: "))
total_food = float(input("Enter the total food units available: "))

# Fixed ration allocation
ration_per_colonist = 4.0
total_ration = ration_per_colonist * colonists
remaining_stockpile = total_food - total_ration

# Tiered leadership bonuses
zerin_bonus = 0.15 * remaining_stockpile
after_zerin = remaining_stockpile - zerin_bonus

lyra_bonus = 0.10 * after_zerin
remaining_after_bonuses = after_zerin - lyra_bonus

# Equal share among all colonists
equal_share = remaining_after_bonuses / colonists

# Compute total shares
zerin_total = ration_per_colonist + zerin_bonus + equal_share
lyra_total = ration_per_colonist + lyra_bonus + equal_share
other_total = ration_per_colonist + equal_share

# Output with 2 decimal places using f-strings
print(f"Zerin's share: {zerin_total:.2f}")
print(f"Lyra's share: {lyra_total:.2f}")
print(f"Share per colonist: {other_total:.2f}")
