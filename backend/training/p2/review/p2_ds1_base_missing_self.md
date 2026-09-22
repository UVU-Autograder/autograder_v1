<!-- p2-review | case=p2_ds1_base_missing_self | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_base_missing_self

**Dessert Shop 1: Inheritance Superclass** · `cascading_failure` · DessertItem.__init__ is missing self, so every class fails on the shared base

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -1,4 +1,4 @@
 class DessertItem:
-    def __init__(self, name: str = ""):
+    def __init__(name: str = ""):
         self.name = name
```

## What the grader reported

- `dessert_item` (DessertItem base class defines name attribute with default ''): `E   NameError: name 'self' is not defined`
- `candy` (Candy inherits DessertItem and defines candy_weight & price_per_pound): `E   TypeError: DessertItem.__init__() takes from 0 to 1 positional arguments but 2 were given`
- `cookie` (Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen): `E   TypeError: DessertItem.__init__() takes from 0 to 1 positional arguments but 2 were given`
- `icecream` (IceCream inherits DessertItem and defines scoop_count & price_per_scoop): `E   TypeError: DessertItem.__init__() takes from 0 to 1 positional arguments but 2 were given`
- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E   TypeError: DessertItem.__init__() takes from 0 to 1 positional arguments but 2 were given`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission has several errors related to how the class constructors are defined and how they interact with inheritance.

**DessertItem base class defines name attribute with default ''**: The __init__ method for DessertItem is missing the 'self' parameter.
- 💡 How should a standard instance method signature be structured in Python?

**Candy inherits DessertItem and defines candy_weight & price_per_pound**: The super() call is passing more arguments than the DessertItem constructor is set up to receive.
- 💡 If DessertItem's __init__ only accepts one argument (besides self), how many arguments should you pass to super().__init__()?

**Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen**: This error follows the same pattern as the Candy class.
- 💡 Review the number of arguments your superclass constructor accepts.

**IceCream inherits DessertItem and defines scoop_count & price_per_scoop**: This error follows the same pattern as the Candy class.
- 💡 Review the number of arguments your superclass constructor accepts.

**Sundae inherits IceCream and defines topping_name & topping_price**: This error follows the same pattern as the Candy class.
- 💡 Review the number of arguments your superclass constructor accepts.

**Next step:** Review the definition of the __init__ method in the DessertItem class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessert_item`, `candy`, `cookie`, `icecream`, `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The Candy item blamed the super() call, and its hint would lead a student to break working code. The only bug is DessertItem.__init__ missing self. Cut to 3 items; the others follow from the base class.

status: todo

```json
{
  "summary": "Your subclasses all pass their values up to DessertItem, which is the right design. One problem in the base class is breaking every class at once.",
  "items": [
    {
      "test_key": "dessert_item",
      "what_went_wrong": "Creating a DessertItem fails with \"name 'self' is not defined\".",
      "hint": "Compare the first line of DessertItem.__init__ with the __init__ of any other class in your file. What is different?"
    },
    {
      "test_key": "candy",
      "what_went_wrong": "Candy's super().__init__(name) call is fine; it fails because it reaches the broken DessertItem constructor.",
      "hint": "This follows from the DessertItem problem. Fix that first."
    },
    {
      "test_key": "cookie",
      "what_went_wrong": "Same cause as Candy: the shared DessertItem constructor.",
      "hint": "This clears once DessertItem.__init__ is fixed."
    }
  ],
  "next_step": "Look closely at DessertItem.__init__, then rerun the tests. IceCream and Sundae fail for the same reason."
}
```
