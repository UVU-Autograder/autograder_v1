"""Module 2 Project 1: Resource Allocation System - ARC-9 Dispenser Protocol."""

# Collect fleet inputs
citizens = int(input("How many citizens: "))
total_units = float(input("How many total units: "))

# Pre-allocation: Citizens except Mira and Tov receive 3 units
shore_leave_units = 3.0
shore_leave_citizens = max(0, citizens - 2)
pre_allocated_total = shore_leave_citizens * shore_leave_units
remaining_supply = total_units - pre_allocated_total

# Mira receives 13% of the remaining supply
mira_bonus = round(0.13 * remaining_supply, 2)
supply_after_mira = remaining_supply - mira_bonus

# Tov receives 11% of what remains after Mira
tov_bonus = round(0.11 * supply_after_mira, 2)
final_remaining = supply_after_mira - tov_bonus

# Equal split among all citizens (including Mira and Tov)
equal_share = round(final_remaining / citizens, 2)

# Final shares
mira_share = mira_bonus + equal_share
tov_share = tov_bonus + equal_share
crew_share = shore_leave_units + equal_share

# Display formatted results to 2 decimal places
print(f"Mira's share: {mira_share:.2f}")
print(f"Tov's share: {tov_share:.2f}")
print(f"Crew's share: {crew_share:.2f}")
