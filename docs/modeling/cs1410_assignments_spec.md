# CS 1410 — Complete Assignment Specification

This document is the single source of truth for modeling all 17 CS 1410 assignments in the autograder. It maps every assignment's class structures, required files, grading criteria, and autograding strategy. Use this spec when authoring `config_json`, `tests.py`, and model solutions during Phase B implementation.

---

## Table of Contents

- [Course-Level Settings](#course-level-settings)
- [Dessert Shop Chain (ds1–ds10)](#dessert-shop-chain-ds1ds10)
  - [DS1: Inheritance](#ds1-inheritance-module-3)
  - [DS2: Using Classes in main](#ds2-using-classes-in-main-module-4)
  - [DS3: Test Cases with pytest](#ds3-test-cases-with-pytest-module-5)
  - [DS4: Abstraction](#ds4-abstraction-module-6)
  - [DS5: Console Application](#ds5-console-application-module-7)
  - [DS6: Overriding Methods](#ds6-overriding-methods-module-8)
  - [DS7: Mixin Interface](#ds7-mixin-interface-module-9)
  - [DS8: Payment Method](#ds8-payment-method-module-10)
  - [DS9: Sort Receipt Items](#ds9-sort-receipt-items-module-11)
  - [DS10: Combine Like Items](#ds10-combine-like-items-module-12)
- [Standalone Labs (lab1–lab7)](#standalone-labs-lab1lab7)
  - [Lab 1: Image Processing](#lab-1-image-processing-module-1)
  - [Lab 2: Bank Account Class](#lab-2-bank-account-class-module-2)
  - [Lab 3: Type Hinting and Encapsulation](#lab-3-type-hinting-and-encapsulation-module-2)
  - [Lab 4: Properties and Validation](#lab-4-properties-and-validation-module-3)
  - [Lab 5: Operator Overloading](#lab-5-operator-overloading-module-3)
  - [Lab 6: Pygame Animation](#lab-6-pygame-animation-module-8)
  - [Lab 7: Data Classes](#lab-7-data-classes-module-11)
- [Cumulative Class Hierarchy](#cumulative-class-hierarchy)
- [Autograding Strategy Matrix](#autograding-strategy-matrix)

---

## Course-Level Settings

| Setting | Value |
|---------|-------|
| Course code | `cs1410` |
| Default concepts | `["variables", "conditionals", "loops", "functions"]` |
| Sandbox enabled | `true` (global) |
| Language | `python` |
| Tax rate (Dessert Shop) | `7.25%` (used in DS4+) |

### Module Concept Mappings

The effective allowed concepts for any assignment are the union of the course-level **Default concepts** and the assignment's **Module concepts**:

| Module | Concepts |
|--------|----------|
| **Module 1: Warmup** | `["image-processing"]` |
| **Module 2: Object-Oriented Intro** | `["classes", "type-hints"]` |
| **Module 3: Inheritance, Polymorphism, and Properties** | `["inheritance", "properties", "operator-overloading"]` |
| **Module 4: Generators and Iterators** | `["generators"]` |
| **Module 5: Unit Tests with pytest** | `["testing"]` |
| **Module 6: Abstract Classes** | `["abstract-classes", "operator-overloading"]` |
| **Module 7: Exceptions and Protocols** | `["exceptions", "protocols"]` |
| **Module 8: Introduction to Pygame** | `["pygame"]` |
| **Module 9: Object-Oriented Pygame** | `["classes"]` |
| **Module 10: Pygame GUI Widgets** | `[]` |
| **Module 11: Named tuples, Dataclasses, and Sorting lists** | `["dataclasses", "file-io"]` |
| **Module 12: CS Degrees at UVU** | `[]` |

---

## Dessert Shop Chain (ds1–ds10)

The Dessert Shop is a single progressive codebase that students build across 10 modules. Each part adds new OOP concepts to the same class hierarchy. The **file count grows** from 1 file (DS1) to 11 files (DS10).

### File Count Evolution

| Part | Files | New Files |
|------|-------|-----------|
| DS1 | 1 | `dessert.py` |
| DS2 | 2 | `dessertshop.py` |
| DS3 | 3 | `test_dessert.py` |
| DS4 | 7 | `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py` |
| DS5 | 7 | (same; `dessertshop.py` updated) |
| DS6 | 7 | (same; `__str__` and `to_list` added) |
| DS7 | 8 | `packaging.py` |
| DS8 | 10 | `payment.py`, `test_order.py` |
| DS9 | 10 | (same; relational operators added) |
| DS10 | 11 | `combine.py` |

---

### DS1: Inheritance (Module 3)

**Slug:** `ds1` · **Required files:** `dessert.py` · **Points:** 100

#### Class Hierarchy
```
DessertItem
├── Candy
├── Cookie
├── IceCream
│   └── Sundae
```

#### Class Specifications

| Class | Attribute | Type | Default |
|-------|-----------|------|---------|
| `DessertItem` | `name` | `str` | `""` |
| `Candy` | `name` | `str` | `""` |
| | `candy_weight` | `float` | `0.0` |
| | `price_per_pound` | `float` | `0.0` |
| `Cookie` | `name` | `str` | `""` |
| | `cookie_quantity` | `int` | `0` |
| | `price_per_dozen` | `float` | `0.0` |
| `IceCream` | `name` | `str` | `""` |
| | `scoop_count` | `int` | `0` |
| | `price_per_scoop` | `float` | `0.0` |
| `Sundae` | `name` | `str` | `""` |
| | `scoop_count` | `int` | `0` |
| | `price_per_scoop` | `float` | `0.0` |
| | `topping_name` | `str` | `""` |
| | `topping_price` | `float` | `0.0` |

#### Key Requirements
- All constructors call `super().__init__()`.
- `Sundae` inherits from `IceCream`, **not** `DessertItem`.
- No output; no `main()`.

#### Autograding Strategy
**Fully automated.** Tests verify:
1. Class existence and inheritance (`issubclass`)
2. Default attribute values (construct with no args)
3. Parameterized attribute values (construct with args)
4. Attribute mutability (set, then assert)
5. `super()` chain (`Sundae → IceCream → DessertItem`)

#### Pytest Markers & Points
| Marker | Label | Points |
|--------|-------|--------|
| `ag_dessert_item` | DessertItem superclass | 20 |
| `ag_candy` | Candy class | 20 |
| `ag_cookie` | Cookie class | 20 |
| `ag_icecream` | IceCream class | 20 |
| `ag_sundae` | Sundae class (inherits IceCream) | 20 |

#### Testing Student Submissions
To test and verify student submissions locally or via automated sandbox test scripts:
1. Bundle the student's `dessert.py` file into a ZIP archive (e.g. `submission.zip`).
2. Run a grading run using the `ds1` configuration and `tests.py` as the test suite.
3. Verify that:
   - A correct implementation (matching `backend/app/db/seeds/ds1/dessert.py`) passes all tests (100/100 points, 0 warnings/failures).
   - Incorrect implementations (e.g. missing `super().__init__()` calls, incorrect inheritance, incorrect attribute defaults, or incorrect types) trigger the corresponding test failures and reduce the score accordingly.

---

### DS2: Using Classes in main (Module 4)

**Slug:** `ds2` · **Required files:** `dessert.py`, `dessertshop.py` · **Points:** 100

#### New Class: `Order` (in `dessert.py`)

| Attribute | Type | Default |
|-----------|------|---------|
| `order` | `list` | `[]` |

| Method | Signature | Notes |
|--------|-----------|-------|
| `add` | `(self, item)` | Appends item to order list |
| `__len__` | `(self) -> int` | Returns number of items |
| `__iter__` | `(self)` | Resets position, returns self |
| `__next__` | `(self)` | Returns next item or raises `StopIteration` |

#### `main()` in `dessertshop.py`
Creates an `Order` with 6 hardcoded items and prints each name + total count.

#### Autograding Strategy
**Fully automated.** Tests verify:
1. All DS1 class tests still pass (regression)
2. `Order` class exists with `add`, `__len__`, `__iter__`, `__next__`
3. `main()` output matches expected (stdout capture)

#### Pytest Markers & Points
| Marker | Label | Points |
|--------|-------|--------|
| `ag_ds1_regression` | DS1 class hierarchy intact | 20 |
| `ag_order_class` | Order class structure & methods | 40 |
| `ag_main_output` | main() produces correct output | 40 |

---

### DS3: Test Cases with pytest (Module 5)

**Slug:** `ds3` · **Required files:** `dessert.py`, `dessertshop.py`, `test_dessert.py` · **Points:** 100

#### Key Requirements
- Student writes 15 pytest tests (3 per class: default, provided, updated values).
- No code changes to existing classes.

#### Autograding Strategy
**Hybrid.** We verify:
1. `test_dessert.py` exists and contains ≥15 test functions
2. Student's tests pass when run against their own code
3. DS2 regression (Order + classes intact)

| Marker | Label | Points |
|--------|-------|--------|
| `ag_test_file_exists` | test_dessert.py present with ≥15 tests | 30 |
| `ag_student_tests_pass` | Student's own tests pass | 40 |
| `ag_ds2_regression` | DS2 class hierarchy + Order intact | 30 |

---

### DS4: Abstraction (Module 6)

**Slug:** `ds4` · **Required files:** `dessert.py`, `dessertshop.py`, `test_dessert.py`, `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py` · **Points:** 100

#### Evolutionary Changes
- `DessertItem` becomes `ABC` with abstract `calculate_cost()`.
- New `tax_percent: float = 7.25` attribute on `DessertItem`.
- Concrete `calculate_tax()` method on `DessertItem`.
- `Order` gets `order_cost()` and `order_tax()`.
- Receipt printed via `tabulate` with `"fsql"` format.

#### Cost Formulas
| Class | Formula |
|-------|---------|
| `Candy` | `round(candy_weight * price_per_pound, 2)` |
| `Cookie` | `round((cookie_quantity / 12) * price_per_dozen, 2)` |
| `IceCream` | `round(scoop_count * price_per_scoop, 2)` |
| `Sundae` | `round((scoop_count * price_per_scoop) + topping_price, 2)` |

#### Tax Formula (all classes)
`round(calculate_cost() * (tax_percent / 100), 2)`

#### Autograding Strategy
**Fully automated.** Tests verify:
1. `DessertItem` is abstract (cannot instantiate)
2. `tax_percent` defaults to `7.25`
3. `calculate_cost()` returns correct values for known inputs
4. `calculate_tax()` returns correct values for known inputs
5. `Order.order_cost()` and `Order.order_tax()` sum correctly

| Marker | Label | Points |
|--------|-------|--------|
| `ag_abstract_class` | DessertItem is ABC with abstract calculate_cost | 15 |
| `ag_tax_percent` | tax_percent attribute defaults to 7.25 | 10 |
| `ag_calculate_cost` | calculate_cost() correct for all subclasses | 30 |
| `ag_calculate_tax` | calculate_tax() correct for all subclasses | 20 |
| `ag_order_totals` | order_cost() and order_tax() correct | 25 |

---

### DS5: Console Application (Module 7)

**Slug:** `ds5` · **Required files:** `dessert.py`, `dessertshop.py`, `test_dessert.py`, `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py` · **Points:** 100

#### New Class: `DessertShop` (in `dessertshop.py`)

| Method | Returns | Prompts For |
|--------|---------|-------------|
| `user_prompt_candy` | `Candy` | name, weight, price_per_pound |
| `user_prompt_cookie` | `Cookie` | name, quantity, price_per_dozen |
| `user_prompt_icecream` | `IceCream` | name, scoop_count, price_per_scoop |
| `user_prompt_sundae` | `Sundae` | name, scoops, price_per_scoop, topping_name, topping_price |

#### Autograding Strategy
**Partially automated.** Interactive prompts make full stdin/stdout matching fragile. We test:
1. `DessertShop` class exists with all 4 methods
2. DS4 regression (ABC, cost/tax formulas)
3. Manual rubric for input validation quality

| Marker | Label | Points | Type |
|--------|-------|--------|------|
| `ag_dessertshop_class` | DessertShop class with 4 prompt methods | 30 | pytest |
| `ag_ds4_regression` | DS4 ABC + cost/tax intact | 30 | pytest |
| `input_validation` | Input validation quality | 20 | manual |
| `receipt_output` | Receipt format and correctness | 20 | manual |

---

### DS6: Overriding Methods (Module 8)

**Slug:** `ds6` · **Required files:** `dessert.py`, `dessertshop.py`, `test_dessert.py`, `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py` · **Points:** 100

#### Evolutionary Changes
- `__str__` methods added to `Candy`, `Cookie`, `IceCream`, `Sundae`, `Order`.
- `Order.to_list()` method added for tabulate rendering.
- `main()` updated with interactive `match/case` menu.

#### Autograding Strategy
**Partially automated.** `__str__` format is fragile to test exactly. We test structure and cost correctness, with manual review for output formatting.

| Marker | Label | Points | Type |
|--------|-------|--------|------|
| `ag_str_methods` | __str__ defined on all dessert classes | 25 | pytest |
| `ag_to_list` | Order.to_list() returns correct 2D list | 25 | pytest |
| `ag_ds5_regression` | DS5 classes + DessertShop intact | 20 | pytest |
| `output_format` | Receipt formatting matches spec | 30 | manual |

---

### DS7: Mixin Interface (Module 9)

**Slug:** `ds7` · **Required files:** `dessert.py`, `dessertshop.py`, `packaging.py`, `test_dessert.py`, `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py` · **Points:** 100

#### New File: `packaging.py`
```python
from typing import Protocol
class Packaging(Protocol):
    packaging: str
```

#### Evolutionary Changes
- `DessertItem(ABC, Packaging)` — adds `self.packaging = None`.
- Subclass defaults: Candy→`"Bag"`, Cookie→`"Box"`, IceCream→`"Bowl"`, Sundae→`"Boat"`.
- `__str__` updated to include `(packaging)` after item name.

#### Autograding Strategy
**Fully automated.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_packaging_protocol` | Packaging Protocol exists in packaging.py | 15 |
| `ag_packaging_defaults` | Default packaging values correct per class | 25 |
| `ag_packaging_in_str` | __str__ includes packaging in output | 25 |
| `ag_ds6_regression` | DS6 classes + __str__ + to_list intact | 35 |

---

### DS8: Payment Method (Module 10)

**Slug:** `ds8` · **Required files:** `dessert.py`, `dessertshop.py`, `packaging.py`, `payment.py`, `test_dessert.py`, `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py`, `test_order.py` · **Points:** 100

#### New File: `payment.py`
```python
from typing import Protocol, Literal
PayType = Literal["CASH", "CARD", "PHONE"]
class Payable(Protocol):
    def get_pay_type(self) -> PayType: ...
    def set_pay_type(self, payment_method: PayType) -> None: ...
```

#### Evolutionary Changes
- `Order` implements `Payable` with `get_pay_type()`, `set_pay_type()`.
- `Order.__init__` adds `self.pay_type = "CASH"`.
- `ValueError` raised for invalid payment types.
- New `test_order.py` with 5 required tests.

#### Autograding Strategy
**Fully automated.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_payment_protocol` | PayType + Payable in payment.py | 15 |
| `ag_order_payable` | Order implements get/set_pay_type with validation | 30 |
| `ag_student_order_tests` | Student's test_order.py exists with ≥5 tests | 20 |
| `ag_ds7_regression` | DS7 packaging + classes intact | 35 |

---

### DS9: Sort Receipt Items (Module 11)

**Slug:** `ds9` · **Required files:** same as DS8 (10 files) · **Points:** 100

#### Evolutionary Changes
- `DessertItem` gets 6 relational operators (`__eq__`, `__ne__`, `__lt__`, `__gt__`, `__le__`, `__ge__`) comparing by `calculate_cost()`.
- `Order.sort()` sorts items by cost ascending.

#### Autograding Strategy
**Fully automated.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_relational_ops` | All 6 relational operators on DessertItem | 30 |
| `ag_order_sort` | Order.sort() sorts by cost ascending | 25 |
| `ag_student_sort_tests` | Student tests for operators + sort exist | 20 |
| `ag_ds8_regression` | DS8 payment + packaging intact | 25 |

---

### DS10: Combine Like Items (Module 12)

**Slug:** `ds10` · **Required files:** `dessert.py`, `dessertshop.py`, `packaging.py`, `payment.py`, `combine.py`, `test_dessert.py`, `test_candy.py`, `test_cookie.py`, `test_icecream.py`, `test_sundae.py`, `test_order.py` · **Points:** 100

#### New File: `combine.py`
```python
from typing import Protocol, runtime_checkable
@runtime_checkable
class Combinable(Protocol):
    def can_combine(self, other: "Combinable") -> bool: ...
    def combine(self, other: "Combinable") -> "Combinable": ...
```

#### Evolutionary Changes
- `Candy` and `Cookie` implement `Combinable` **structurally** (duck typing, no inheritance).
- `can_combine`: True if same type, same name, same unit price.
- `combine`: Adds quantities/weights together, returns `self`.
- `Order.add()` checks for combinable items before appending.

#### Autograding Strategy
**Fully automated.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_combinable_protocol` | Combinable Protocol in combine.py (@runtime_checkable) | 15 |
| `ag_candy_combinable` | Candy can_combine + combine correct | 20 |
| `ag_cookie_combinable` | Cookie can_combine + combine correct | 20 |
| `ag_order_combine` | Order.add() merges combinable items | 20 |
| `ag_ds9_regression` | DS9 sort + relational ops intact | 25 |

---

## Standalone Labs (lab1–lab7)

### Lab 1: Image Processing (Module 1)

**Slug:** `lab-1-image-processing` · **Required files:** `bears2.py`, `bears3.py`, `bears2.jpg`, `bears3.jpg` · **Points:** 100

#### Autograding Strategy
**Fully automated with manual grading.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_part1_files` | Part 1 required files are present | 15 |
| `ag_part1_output` | Part 1 script regenerates a valid non-trivial `bears2.jpg` from `bears_copy.jpg` | 15 |
| `ag_part2_files` | Part 2 required files are present | 15 |
| `ag_part2_output` | Submitted `bears3.jpg` opens and contains non-trivial pixels | 15 |
| (manual) | Part 1: Subjective filter visual quality | 20 |
| (manual) | Part 2: Subjective balloon composite quality & placement | 20 |

#### Testing Student Submissions
To test and verify student submissions locally or via automated sandbox test scripts:
1. Bundle the student's submission files (`bears2.py`, `bears3.py`, `bears2.jpg`, `bears3.jpg`) into a ZIP archive (e.g. `submission.zip`).
2. Run a grading run using the `lab-1-image-processing` configuration and `tests.py` as the test suite.
3. Verify that:
   - A correct implementation passes all tests (60/60 automated points, 0 warnings/failures).
   - Part 1 re-executes `bears2.py` against injected `bears_copy.jpg` (per lab writeup).
   - Part 2 validates the submitted `bears3.jpg` only — students may use any online balloon image and are not required to submit it.
   - Incorrect implementations or missing files trigger test failures or blocked concepts (e.g. if they attempt to import blocked packages).
4. Run verification tests against a representative set of actual student submissions (e.g. using `.agents/scratch/run_lab1_submissions.py`) to confirm that:
   - The allowed concepts list includes the course default concepts (`["variables", "conditionals", "loops", "functions"]`) in addition to module-level concepts, preventing false positive warnings.
   - Student submissions wrapping logic in `if __name__ == "__main__":` execute correctly by using `run_name="__main__"` in `runpy.run_path`.
   - Student submissions with security-restricted imports (e.g., `os`) are correctly blocked.
   - Path-based discrepancies for Part 1 (e.g., hardcoded subdirectories or not using `bears_copy.jpg`) are caught as test failures.

---

### Lab 2: Bank Account Class (Module 2)

**Slug:** `lab2` · **Required files:** `account.py`, `demo.py` · **Points:** 100

#### Class: `Account`
| Attribute | Type | Default |
|-----------|------|---------|
| `owner` | `str` | `""` |
| `balance` | `float` | `0.0` |

| Method | Returns | Format |
|--------|---------|--------|
| `__str__` | `str` | `"Owner: {owner}, Balance: ${balance:.2f}"` |

#### Autograding Strategy
**Fully automated.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_account_init` | Account class with defaults | 40 |
| `ag_account_str` | __str__ format correct | 30 |
| `ag_demo_output` | demo.py produces correct output | 30 |

---

### Lab 3: Type Hinting and Encapsulation (Module 2)

**Slug:** `lab3` · **Required files:** `youtube_channel.py`, `Lab3_reflection.md` · **Points:** 100

#### Class: `YouTubeChannel`
| Attribute | Type | Default | Visibility |
|-----------|------|---------|------------|
| `_name` | `str` | `""` | protected (`_`) |
| `__video_count` | `int` | `0` | private (`__`) |

| Method | Signature | Notes |
|--------|-----------|-------|
| `__str__` | `-> str` | `"Channel: {_name}, Videos: {__video_count}"` |
| `get_name` | `-> str` | Returns `_name` |
| `get_video_count` | `-> int` | Returns `__video_count` |
| `set_name` | `(name: str)` | Sets `_name` |
| `set_video_count` | `(count: int)` | Sets `__video_count`; **ignores negative values** |

#### Autograding Strategy
**Hybrid.** Code structure is testable; reflection is manual.

| Marker | Label | Points | Type |
|--------|-------|--------|------|
| `ag_encapsulation` | _ and __ attributes correct | 20 |pytest |
| `ag_getters_setters` | Getter/setter methods work; negative guard | 30 | pytest |
| `ag_type_hints` | Type hints present on __init__ and __str__ | 20 | pytest |
| `reflection` | Reflection answers (3 questions) | 30 | manual |

---

### Lab 4: Properties and Validation (Module 3)

**Slug:** `lab4` · **Required files:** `book.py`, `Lab4_reflection.md` · **Points:** 100

#### Class: `Book`
| Attribute | Type | Visibility |
|-----------|------|------------|
| `_title` | `str` | private (`_`) |
| `_author` | `str` | private (`_`) |

#### Properties
| Property | Created Via | Setter Validation |
|----------|-------------|-------------------|
| `title` | `property()` built-in | `TypeError` if not str, `ValueError` if empty |
| `author` | `@property` decorator | `TypeError` if not str, `ValueError` if empty |
| `description` | `@property` (read-only) | Returns `"{title} was written by {author}."` |

#### Autograding Strategy
**Hybrid.** Properties and validation are testable; reflection is manual.

| Marker | Label | Points | Type |
|--------|-------|--------|------|
| `ag_title_property` | title property with validation | 30 | pytest |
| `ag_author_property` | author property with validation | 30 | pytest |
| `ag_description_readonly` | description is read-only | 20 | pytest |
| `reflection` | Reflection answer | 20 | manual |

---

### Lab 5: Operator Overloading (Module 3)

**Slug:** `lab5` · **Required files:** `money.py` · **Points:** 100

#### Class: `Money`
| Attribute | Type |
|-----------|------|
| `dollars` | `int` |
| `cents` | `int` |

| Method | Signature | Notes |
|--------|-----------|-------|
| `normalize` | `(self)` | Carries cents ≥ 100 into dollars |
| `__str__` | `-> str` | `"${dollars}.{cents:02d}"` |
| `__add__` | `(self, other) -> Money` | Adds two Money objects |
| `__mul__` | `(self, other) -> Money` | Money × int scalar |
| `__rmul__` | `(self, other) -> Money` | int × Money (delegates to __mul__) |
| `__eq__` | `(self, other) -> bool` | Equal after normalization |

#### Autograding Strategy
**Fully automated.**

| Marker | Label | Points |
|--------|-------|--------|
| `ag_normalize` | normalize carries cents correctly | 10 |
| `ag_str` | __str__ format correct | 10 |
| `ag_add` | __add__ operator | 25 |
| `ag_mul` | __mul__ and __rmul__ operators | 30 |
| `ag_eq` | __eq__ operator (normalized comparison) | 25 |

---

### Lab 6: Pygame Animation (Module 8)

**Slug:** `lab6` · **Required files:** `lab6_part1.py`, `lab6_part2.py`, animal image · **Points:** 100

#### Description
Two procedural Pygame scripts animating an animal image bouncing left/right. Part 1 uses raw `(x, y)` variables; Part 2 uses `pygame.Rect`.

#### Autograding Strategy
**Hybrid.** Pygame runs headlessly with SDL dummy drivers. AST analysis verifies the required API coordinates.

| Marker | Label | Points | Type |
|--------|-------|--------|------|
| `ag_part1_ast_execution` | Part 1 headless execution & uses x/y variables (no Rect) | 30 | pytest |
| `ag_part2_ast_execution` | Part 2 headless execution & uses pygame.Rect | 30 | pytest |
| `visual_movement` | Animal bounces off borders smoothly & loops correctly | 40 | manual |

---

### Lab 7: Data Classes (Module 11)

**Slug:** `lab7` · **Required files:** `student.py`, `student_reflection.md` · **Points:** 100

#### Class: `Student` (uses `@dataclass(order=True)`)
| Attribute | Type | Default |
|-----------|------|---------|
| `id` | `int` | (required) |
| `name` | `str` | (required) |
| `major` | `str` | (required) |
| `courses` | `list[str]` | `field(default_factory=list)` |

| Method | Signature | Notes |
|--------|-----------|-------|
| `enroll` | `(self, course: str) -> None` | Appends course to list |
| `total_courses` | `(self) -> int` | Returns len(courses) |

#### Autograding Strategy
**Hybrid.** Data class structure and methods are testable; reflection is manual.

| Marker | Label | Points | Type |
|--------|-------|--------|------|
| `ag_dataclass` | @dataclass(order=True) with correct fields | 20 | pytest |
| `ag_methods` | enroll() and total_courses() work | 25 | pytest |
| `ag_ordering` | Comparison operators work (sorted by id) | 20 | pytest |
| `ag_main_output` | main() creates students, enrolls, prints | 20 | pytest |
| `reflection` | Reflection answers (3 questions) | 15 | manual |

---

## Cumulative Class Hierarchy

The final state of the Dessert Shop class hierarchy at DS10:

```
Packaging (Protocol) ← packaging.py
    attribute: packaging: str

DessertItem(ABC, Packaging) ← dessert.py
    attrs: name, tax_percent=7.25, packaging=None
    abstract: calculate_cost() -> float
    concrete: calculate_tax() -> float
    relational: __eq__, __ne__, __lt__, __gt__, __le__, __ge__ (by cost)
    ├── Candy  [implements Combinable structurally]
    │     attrs: candy_weight, price_per_pound, packaging="Bag"
    │     cost: round(weight × price_per_pound, 2)
    ├── Cookie [implements Combinable structurally]
    │     attrs: cookie_quantity, price_per_dozen, packaging="Box"
    │     cost: round((qty / 12) × price_per_dozen, 2)
    └── IceCream
          attrs: scoop_count, price_per_scoop, packaging="Bowl"
          cost: round(scoops × price_per_scoop, 2)
          └── Sundae
                attrs: topping_name, topping_price, packaging="Boat"
                cost: round((scoops × price_per_scoop) + topping_price, 2)

Order(Payable) ← dessert.py
    attrs: order=[], pay_type="CASH"
    methods: add(), sort(), __len__, __iter__, __next__
    methods: order_cost(), order_tax(), to_list()
    methods: get_pay_type(), set_pay_type()

Payable (Protocol) ← payment.py
Combinable (Protocol, @runtime_checkable) ← combine.py
DessertShop ← dessertshop.py
```

---

## Autograding Strategy Matrix

| Assignment | Automated | Manual | Total | Notes |
|------------|-----------|--------|-------|-------|
| **DS1** | 100 | 0 | 100 | Pure class structure |
| **DS2** | 100 | 0 | 100 | Structure + stdout |
| **DS3** | 100 | 0 | 100 | Student test file validation |
| **DS4** | 100 | 0 | 100 | ABC + cost/tax math |
| **DS5** | 60 | 40 | 100 | Interactive prompts need manual review |
| **DS6** | 70 | 30 | 100 | __str__ format is fragile |
| **DS7** | 100 | 0 | 100 | Protocol + defaults |
| **DS8** | 100 | 0 | 100 | Protocol + validation |
| **DS9** | 100 | 0 | 100 | Operators + sort |
| **DS10** | 100 | 0 | 100 | Combinable protocol |
| **Lab 2** | 100 | 0 | 100 | Simple class |
| **Lab 3** | 70 | 30 | 100 | Reflection is manual |
| **Lab 4** | 80 | 20 | 100 | Reflection is manual |
| **Lab 5** | 100 | 0 | 100 | Pure operator tests |
| **Lab 6** | 60 | 40 | 100 | Headless execution + AST checks (auto), Visual bounce (manual) |
| **Lab 7** | 85 | 15 | 100 | Reflection is manual |

---

## Grading Calibration & Mutation Testing

Grading criteria, rubrics, and automated test accuracy are calibrated and verified against the comprehensive synthetic test mutation suite in [`backend/eval/mutations.py`](../../backend/eval/mutations.py).

For every assignment across Labs 1–7 and Dessert Shop 1–10:
- **Baseline Correctness:** Validated against canonical model solutions located in [`backend/app/db/seeds/`](../../backend/app/db/seeds/).
- **Error & Partial Credit Behavior:** Evaluated against 146+ synthetic mutated submissions covering single-item test failures, import/syntax errors, missing attributes, incorrect return types, calculation deviations, and security injection attempts.
- **Automated Verification:** Verified continuously via [`backend/tests/test_seed_integrity.py`](../../backend/tests/test_seed_integrity.py) and [`backend/tests/test_assignment_validation.py`](../../backend/tests/test_assignment_validation.py).

