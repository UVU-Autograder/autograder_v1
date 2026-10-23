## **Population Growth Simulator - "Gaia Viability Estimator"**

### **Learning Outcomes**

By completing this project, you will:

- **Apply** loops, if statements, and user-defined functions to structure and control the flow of your program.
- **Generate** a sequence of data points that simulate a population over time using mathematical modeling.
- **Utilize** lists to **store** and **manage** population values for each simulation step.
- **Develop** a simple simulation using code to model real-world population growth in a constrained environment.
- **Write** simulation results to an external text file for further analysis and verification.
- **Use** command-line arguments to pass input values to your program, enhancing usability and automation.

### **Mission Brief**

As the Earth entered its final collapse, the last wave of evacuees boarded the *Nova Exodus* fleet -- a generation ship bound for **Gaia-4**, an Earth-like planet capable of supporting human life. However, the planet's biosphere is still unstable, and the colonial council must determine whether its environment can sustain a growing human population.

To assess the viability of the mission, scientists have deployed the **Gaia Viability Estimator** -- a simulation tool based on the *logistic growth model*. Using data from environmental sensors, the estimator projects how a colony's population would grow under resource-constrained conditions on Gaia-4.

### **Project Description**

You will implement a population growth simulator using the **Logistic Equation**, which models how populations grow under limited resources:

$$P_n = r \times P_{n-1} \times (1 - P_{n-1})$$

Where:
- $P_n$ is the population (as a percentage of maximum capacity) at time step $n$
- $r$ is the growth rate
- $P_{n-1}$ is the population at the previous time step

**Your Program Must:**

- Take **4 command line arguments**:
  - Initial population as a percentage of the total population ($0 < p_0 < 1$)
  - Growth rate ($0 < r < 4$)
  - Number of simulation steps (positive integer)
  - Output filename (e.g., `output.txt`)
- Use a **function to compute the next population value**
- Use a **list** to store each time step's population
- Validate inputs (e.g., growth rate in proper range)
- Write the time and population values to the output file with values **rounded to 3 decimal places**
- Have a **main() function** and use `if __name__ == "__main__":` block
- Contain no global execution outside of function calls

### **Example Run**

```bash
python3 gaia_growth_simulator.py 0.1 2.5 20 output.txt
```

**Contents of `output.txt`:**
```text
0   0.100
1   0.225
2   0.436
3   0.615
4   0.592
5   0.604
6   0.598
7   0.601
8   0.600
9   0.600
...
20  0.600
```

### **File Submission**

Submit your file as: `gaia_growth_simulator.py`

### **Key Program Requirements and Rubrics (100 points)**

1. (15 points) Writes output to file, formatted correctly with 3 decimal places
2. (15 points) Works with any valid parameter input
3. (15 points) Uses `for` or `while` loops, if statements, and user-defined functions
4. (5 points) Code is in a file named `gaia_growth_simulator.py`
5. (5 points) Contains a `main()` function with conditional execution
6. (10 points) The Logistic Equation is implemented in its own function
7. (10 points) Correctly parses command line arguments and validates input
8. (10 points) Uses a list to capture all population values over time
9. (10 points) Validates that values are within acceptable ranges
10. (5 points) Follows proper code style (snake_case, variable naming)
