# Module 5: Programming Project - Dessert Shop 3 Test Cases with pytest

Read instructions carefully. Not following instructions will result in you not receiving the credit you want.

Make sure your output matches the sample run.

**Big Note:** The starting point for Part 3 is the files you submitted for Part 2.

# Objectives

In this part of the project, you will:

- Write and run `pytest` test cases for constructors, attributes, and methods.
    

# Structure

- Module name: `dessert`
    
    - Classes
        
        - `DessertItem`
            
        - `Candy`
            
        - `Cookie`
            
        - `IceCream`
            
        - `Sundae`
            
        - `Order`
            
- Module name: `dessertshop`
    
    - Functions
        
        - `main`
            

# Problem

A Dessert Shop sells candy by the pound, cookies by the dozen, ice cream by the scoop, and sundaes (ice cream with a topping).

For Part 3, your task is to create automated test cases for the following classes:

- `DessertItem`
    
- `Candy`
    
- `Cookie`
    
- `IceCream`
    
- `Sundae`
    

Note: You do not need to write tests for the `Order` class.

## Test Cases Requirements

Write three test cases for **each** of the five classes listed above:

1. **Default values:** Verify attributes are initialized with default values.
    
2. **Provided values:** Verify attributes are initialized correctly with given values.
    
3. **Updated values:** Confirm that attributes can be updated and that the changes are reflected correctly.
    

Note:

- All test cases must be implemented using `pytest`.
    
- Save all your test code in the file `test_dessert.py`.
    

# Sample Run

Your output should match that from Part 2. For reference:

Candy Corn  
Gummy Bears  
Chocolate Chip  
Pistachio  
Vanilla  
Oatmeal Raisin  
Total number of items in order: 6

# Grading

Use the following rubric for grading.

| Criteria                       | Mastery (100%)                                                                                                                                | Proficient (85%)                                                                                                       | Developing (70%)                                                                                          | Beginning (60%)                                                                                                   | Not Demonstrated (50%)                                          |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Test Cases**                 | All test cases are correctly written and successfully test all functionalities of the classes. All required tests for each class are present. | Most test cases are correctly written and successfully test most functionalities. A few required tests may be missing. | Some test cases are correctly written and test some functionalities, but many required tests are missing. | Test cases are present, but they are fundamentally flawed and do not test class functionalities correctly.        | No test cases are provided.                                     |
| **Program Output**             | The program's output exactly matches the example output given in the problem statement.                                                       | The program's output mostly matches the example output, with minor discrepancies.                                      | The program's output somewhat matches the example output, but there are major discrepancies.              | The program's output has been attempted but it significantly deviates from the example output.                    | The program does not produce output.                            |
| **Integration of Part 2 Code** | Part 3 correctly builds on Part 2 and includes all relevant code from the previous assignment.                                                | Part 3 includes most of the code from Part 2 with minor omissions.                                                     | Part 3 includes some code from Part 2 but lacks important components.                                     | Part 3 includes very little from Part 2 or the integration is unclear.                                            | Part 3 does not appear to build on Part 2 at all.               |
| **Code Quality**               | Code is clearly written, logically organized, and easy to follow. No syntax errors.                                                           | Code is mostly clear and logically organized, with minor syntax errors that do not affect program execution.           | Code is somewhat clear and organized, but with syntax errors that may affect program execution.           | Code is unclear, disorganized, and contains numerous syntax errors that prevent program from executing correctly. | No code or code cannot be evaluated due to major syntax errors. |

In this rubric, each criterion is evaluated independently and contributes to the overall score for the assignment. For example, if a student’s code has mastery level “Test Cases” (60 points), proficient “Program Output” (51 points), developing “Integration of Part 2 Code” (42 points), and beginning “Code Quality” (36 points), the student’s total score would be the average of these four scores.

# What to Submit

Upload your `dessert.py` , `dessertshop.py`and `test_dessert.py` to Canvas.