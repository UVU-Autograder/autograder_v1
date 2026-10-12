Module 3: Programming Project - Dessert Shop 1 Inheritance
 
Read the instructions carefully. Not following the instructions will result in you not earning the credit you want.

Objectives
Make Python classes to represent items in the real world

Build a superclass

Build several subclasses

Build a project with a 3-level inheritance hierarchy

Structure
Module name: dessert

Class names:

DessertItem

Candy

Cookie

IceCream

Sundae

Problem
A Dessert Shop sells candy by the pound, cookies by the dozen, ice cream by the scoop, and sundaes (ice cream with a topping).

For this part of the project, you will create the structure for a Dessert Shop program. There will be no user interface nor input/output at this time, but there will be later.

To create this framework, you will implement an inheritance hierarchy of classes derived from a DessertItem superclass. Candy, Cookie, and IceCream classes will derive from the DessertItem class. The Sundae class will derive from the IceCream class. The classes will be structured as below.

DessertItem Superclass
The DessertItem superclass contains:

Attribute:

name: str

Default value: an empty string.

A constructor with one parameter that sets the name attribute to the passed-in value.

Derived Subclasses Candy, Cookie, IceCream, and Sundae
All derived subclasses (Candy, Cookie, IceCream, and Sundae) contain:

Attributes as described below

A constructor with enough parameters to initialize all the attributes of the object, including the superclass attribute. The constructor must call the superclass constructor.

The Candy attributes are:

name: str

Default value: an empty string.

candy_weight: float

Default value: 0.0

price_per_pound: float

Default value: 0.0

The Cookie attributes are:

name: str

Default value: an empty string.

cookie_quantity: int

Default value: 0

price_per_dozen: float

Default value: 0.0

The IceCream attributes are:

name: str

Default value: an empty string.

scoop_count: int

Default value: 0

price_per_scoop: float

Default value: 0.0

The Sundae attributes are:

name: str

Default value: an empty string.

scoop_count: int

Default value: 0

price_per_scoop: float

Default value: 0.0

topping_name: str

Default value: an empty string.

topping_price: float

Default value: 0.0

Desserts UML 
![UML](image.png)
 

Shown here is a UML class diagram where attributes have names in snake case and declared types. Specifying types is good in design, even if the language does not require us to explicitly declare the types of variables in our code.

Key Program Requirements
All classes are implemented as above

All these classes are in the file dessert.py.

Sample Run
There is no sample run for this assignment.

Grading
Use the following rubric for grading.

Criteria	Mastery (100%)	Proficient (85%)	Developing (70%)	Beginning (60%)	Not Demonstrated (50%)
DessertItem Superclass	DessertItem superclass correctly includes a name attribute, ensures it has the correct default value, and the constructor properly assigns the name with a passed-in value.	DessertItem superclass is mostly correct, but has minor issues.	DessertItem superclass is present but has major issues with attributes or constructor.	DessertItem superclass has been attempted, but it is fundamentally flawed.	DessertItem superclass does not exist.
Candy Class	Candy class correctly inherits from DessertItem, contains required attributes (name, candy_weight, price_per_pound), ensures all attributes have the correct default values, and its constructor properly initializes all attributes.	Candy class mostly meets requirements but has minor issues with attributes or constructor.	Candy class partially meets requirements but has significant issues with attributes or constructor.	Candy class has been attempted, but it is fundamentally flawed.	Candy class does not exist.
Cookie Class	Cookie class correctly inherits from DessertItem, contains required attributes (name, cookie_quantity, price_per_dozen), ensures all attributes have the correct default values, and its constructor properly initializes all attributes.	Cookie class mostly meets requirements but has minor issues with attributes or constructor.	Cookie class partially meets requirements but has significant issues with attributes or constructor.	Cookie class has been attempted, but it is fundamentally flawed.	Cookie class does not exist.
IceCream Class	IceCream class correctly inherits from DessertItem, contains required attributes (name, scoop_count, price_per_scoop), ensures all attributes have the correct default values, and its constructor properly initializes all attributes.	Ice Cream class mostly meets requirements but has minor issues with attributes or constructor.	Ice Cream class partially meets requirements but has significant issues with attributes or constructor.	Ice Cream class has been attempted, but it is fundamentally flawed.	Ice Cream class does not exist.
Sundae Class	Sundae class correctly inherits from IceCream, contains required attributes (name, scoop_count, price_per_scoop, topping_name, topping_price), ensures all attributes have the correct default values, and its constructor properly initializes all attributes.	Sundae class mostly meets requirements but has minor issues with attributes or constructor.	Sundae class partially meets requirements but has significant issues with attributes or constructor.	Sundae class has been attempted, but it is fundamentally flawed.	Sundae class does not exist.
Implementation of Inheritance	All classes correctly and logically inherit from the appropriate superclasses. Superclass constructors are correctly called in derived class constructors.	Most classes correctly and logically inherit from the appropriate superclasses, but there are minor issues.	Some classes correctly and logically inherit from the appropriate superclasses, but there are significant issues.	Attempt at implementing inheritance is made, but with numerous errors and misunderstanding.	No use or incorrect use of inheritance.
Code Quality	Code is clearly written, logically organized, and easy to follow. No syntax errors.	Code is mostly clear and logically organized, with minor syntax errors that do not affect program execution.	Code is somewhat clear and organized, but with syntax errors that may affect program execution.	Code is unclear, disorganized, and contains numerous syntax errors that prevent program from executing correctly.	No code or code cannot be evaluated due to major syntax errors.
In this rubric, each criterion is evaluated independently and contributes to the overall score for the assignment. For example, if a student’s code has mastery level “DessertItem Superclass” (60 points), proficient “Candy Class” (51 points), developing “Cookie Class” (42 points), beginning “Ice Cream Class” (36 points), proficient “Sundae Class” (51 points), proficient “Implementation of Inheritance” (51 points), and developing “Code Quality” (42 points), the student’s total score would be the average of these seven scores.

What to Submit
Upload your dessert.py file to Canvas.