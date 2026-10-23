## Resource Allocation System - "ARC-9 Dispenser Protocol"

Read all instructions carefully. Not following instructions will result in you not earning the score you want on this assignment.

### **Learning Outcomes**

In completing this project, you will learn the following:

- Use basic statements, expressions, and basic data types (int, float, string) in a program.
- Convert strings to integers or floats and use these values in calculations.
- Read keyboard input from the user and use it in a program.
- Print formatted output using f-strings, ensuring correct rounding and precision.

### **Project Description**

ARC-9 is the autonomous redistribution console aboard the Nova Exodus fleet, a massive armada of ships fleeing a dying Earth. With finite food, fuel, and supplies, fair and strategic allocation of resources is essential to prevent unrest during the multi-decade journey to the new home planet, Nova Gaia. As part of this system, crew members receive a small personal share during shore leave -- the pre-allocation process. Following this, ARC-9 takes over the redistribution process, ensuring that all resources are divided fairly (though some elite officers are secretly prioritized).

Here's how the process works:

Crew members (Except Mira and Tov, since they are too generous) receive 3 units for shore leave. Mira, the high-ranking captain, receives 13% of the remaining supply. Tov, her second-in-command, then receives 11% of what remains after Mira's share. The rest is evenly split among all crew members, including Mira and Tov. The civilians(crews) do not know that Mira and Tov secretly receive larger shares beforehand.

Your task is to build a program that mimics this resource allocation process, helping to ensure a smooth, fair, and transparent redistribution system for the fleet.

**Your Program Must:**

- Ask the user to input:
  - Total number of citizens aboard the fleet (including Mira and Tov)
  - Total amount of resources available (in units)

- Then calculate and display:
  - **Mira's share** (rounded to 2 decimal places)
  - **Tov's share** (rounded to 2 decimal places)
  - **Crew's share** per citizen (rounded to 2 decimal places)

### **Key Program Requirements and Rubrics**

1. (35 points) Results of the various amounts to be calculated are correct to 2 decimal places.
2. (35 points) The program works correctly for different numbers of crew and units, not just the example run.
3. (5 points) Input prompts match what is shown in the example run exactly. For example `How many citizens:`
4. (5 points) Output strings for each amount match the output shown in the example run exactly. For example `Mira's share:` followed by the amount.
5. (5 points) Values are rounded to 2 decimal places.
6. (5 points) All variable names and the code follows Python snake case or camelcase.
7. (5 points) Pay attention to whitespace, punctuation and wording in your prompts and output.
8. (5 points) f-strings for units should be formatted to 2 decimal places for display.

### **Example Run**

`How many citizens: 20 `
`How many total units: 1000 `
`Mira's share: 159.60 `
`Tov's share: 127.15 `
`Crew's share: 39.62`

### **File Submission**

Submit your file as: `resource_allocator.py`
