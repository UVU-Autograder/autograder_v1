## **Submit | Track Bacteria Growth Over Time**

### **Objective**

Write a simple Python program that models how bacteria multiply over time with a fixed growth rate. You'll store the population at each step in a list and display the result.

### **Instruction**

- Ask the user for:
  - Starting population size (a number like `100`)
  - Growth rate per hour (e.g., `1.2` means population grows by 20% every hour)
  - Number of hours to simulate

- Create an empty list called `population_history`.

- Use a loop to calculate and store the population at each hour:
  - For each hour, multiply the previous population by the growth rate.
  - Round the result to 2 decimal places.
  - Add each value to the list.

- After the loop, print each hour and the population size from the list.

### **Sample Input / Output**

```text
Enter starting population: 100
Enter hourly growth rate: 1.2
Enter number of hours: 5

Hour 0: 100.00
Hour 1: 120.00
Hour 2: 144.00
Hour 3: 172.80
Hour 4: 207.36
Hour 5: 248.83
```

### **File Submission**

Submit your file as: `bacteria_growth.py`

### **Grading Rubric (10 points)**

- **2 points** - Uses `input()` to gather all three values from the user
- **2 points** - Creates and appends to a list to track population over time
- **3 points** - Uses correct loop logic to calculate and update population
- **2 points** - Output is clear and uses 2 decimal formatting
- **1 point** - Code runs without syntax errors and includes at least one comment
