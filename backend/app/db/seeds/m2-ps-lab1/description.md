## **Submit | Festival Resource Distribution - Percent Allocations**

### **Objective**

Expand the festival scenario by applying tiered percentage allocations to leaders and then fairly redistributing the remaining supplies among all colonists.

### 🪐 **Characters:**

- **Zerin** - Festival Coordinator
- **Lyra** - Logistics Officer

They receive slightly larger secret shares before the rest of the supplies are distributed.

### **Instruction**

- Prompt the user to enter:
  - Total number of colonists
  - Total amount of food supplies (in units)

- Use your previous calculations to determine:
  - Total **ration** needed: `4 units × number of colonists`
  - Remaining festival stockpile: `total units - ration amount`

- Then apply the following distribution:
  - **Zerin** receives **15%** of the remaining stockpile
  - **Lyra** receives **10%** of what's left *after Zerin's share is subtracted*
  - The rest is evenly divided among all colonists (including Zerin and Lyra)

- Output each share using **f-strings**, rounded to **2 decimal places**:
  - **Zerin's total share** = ration + bonus + equal share
  - **Lyra's total share** = ration + bonus + equal share
  - **Each other colonist's total share** = ration + equal share

### **Sample Input/ Output**

`Enter the number of colonists: 25  `
`Enter the total food units available: 1200`

`Zerin's share: 202.66  `
`Lyra's share: 131.16  `
`Share per colonist: 37.66`

### **File Submission**

- Submit your Python file as: `festival_distribution.py`

### **Grading Rubric (10 points)**

- **2 pts** - Correct calculation of Zerin's 15% share
- **2 pts** - Correct calculation of Lyra's 10% share
- **3 pts** - Proper even distribution of remaining supplies
- **2 pts** - f-strings with formatting to 2 decimal places
- **1 pt** - Clear comments and valid naming conventions
