# Module 11: Lab 7 - Modeling College Students with Data Classes

As part of a campus system upgrade, you’ve been asked to model student information using modern Python features. In this lab, you will use Python’s `@dataclass` decorator to represent students and implement functionality such as enrolling in courses and calculating total credit hours. You’ll also learn how to safely use mutable attributes—like lists—inside data classes.

## Learning Objectives

By the end of this lab, you will be able to:

1. Define a Python data class with multiple typed fields to model structured data.
    
2. Safely use a mutable list attribute with `default_factory` in a data class.
    

## Part 1: Define the `Student` Class (40 points)

1. (15 points) Create a data class named `Student` with the following fields:
    
    - `id: int` – a unique ID for each student (used for sorting)
        
    - `name: str` – the full name of the student
        
    - `major: str` – the student’s declared major
        
    - `courses` – a list of course numbers the student is enrolled in (e.g., `"CS 2300"`, `"CS 2420"`).
        
        - This should default to an empty list.
            
        - Be sure to use `default_factory` to safely initialize this list.
            
2. (5points) Add `order=True` to the data class so that students can be sorted by all attributes. In practice, since each student has a unique `id`, this enables sorting by `id`.
    
3. (20 points) Add the following methods to the class:
    
    - `enroll(self, course: str)`: Adds a course number to the `courses` list.
        
    - `total_courses(self)`: Returns the number of enrolled courses.
        

## Part 2: Create and Use Student Objects (45 points)

In the `main` function, follow the steps below to test your code:

1. Create at least three `Student` objects with different IDs, names, and majors.
    
2. Use the `enroll()` method to add 2–3 course numbers for each student.
    
3. Print each student using `print(student)`. (This will automatically use the default string representation provided by the data class.)
    
4. Print the total number of courses each student is taking using `total_courses()`.
    
5. Write simple comparison code to confirm that sorting works, such as:
    
    - `print(student1 > student2)`
        
    - `print(student2 < student3)`
        

## Part 3: Reflection Questions (15 points)

Answer the following in comments or in a separate markdown file or cell:

1. Why do we use `default_factory` when initializing a list field in a data class?
    
2. What could go wrong if multiple students shared the same default list?
    
3. How does putting methods like `enroll` and `total_courses` inside the class help with code organization?
    

## What to Submit

Submit the following two files to Canvas:

- `student.py`: containing your `Student` class and sample test code from Part 2
    
- `student_reflection.md`: containing your answers to the reflection questions