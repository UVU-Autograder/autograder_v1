<!-- p2-review | case=p2_ds1_placeholder | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_placeholder

**Dessert Shop 1: Inheritance Superclass** · `empty_submission` · dessert.py is a docstring and TODO only

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -1,31 +1,2 @@
-class DessertItem:
-    def __init__(self, name: str = ""):
-        self.name = name
-
-
-class Candy(DessertItem):
-    def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
-        super().__init__(name)
-        self.candy_weight = candy_weight
-        self.price_per_pound = price_per_pound
-
-
-class Cookie(DessertItem):
-    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0):
-        super().__init__(name)
-        self.cookie_quantity = cookie_quantity
-        self.price_per_dozen = price_per_dozen
-
-
-class IceCream(DessertItem):
-    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
-        super().__init__(name)
-        self.scoop_count = scoop_count
-        self.price_per_scoop = price_per_scoop
-
-
-class Sundae(IceCream):
-    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
-        super().__init__(name, scoop_count, price_per_scoop)
-        self.topping_name = topping_name
-        self.topping_price = topping_price
+"""Dessert Shop 1."""
+# TODO: DessertItem, Candy, Cookie, IceCream, Sundae
```

## What the grader reported

- `dessert_item` (DessertItem base class defines name attribute with default ''): `(no message)`
- `candy` (Candy inherits DessertItem and defines candy_weight & price_per_pound): `(no message)`
- `cookie` (Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen): `(no message)`
- `icecream` (IceCream inherits DessertItem and defines scoop_count & price_per_scoop): `(no message)`
- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `(no message)`
- The prompt carries SUBMISSION_NOTE: the code is empty or a placeholder.

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

The file is still a placeholder, as it currently only contains comments and docstrings.

**DessertItem base class defines name attribute with default ''**: The DessertItem base class is missing the required name attribute with a default value.
- 💡 How can you define a class attribute in the base class?

**Candy inherits DessertItem and defines candy_weight & price_per_pound**: The Candy class does not correctly inherit from DessertItem or define the required attributes.
- 💡 What syntax is used to inherit from a parent class and define new attributes?

**Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen**: The Cookie class does not correctly inherit from DessertItem or define the required attributes.
- 💡 What syntax is used to inherit from a parent class and define new attributes?

**IceCream inherits DessertItem and defines scoop_count & price_per_scoop**: The IceCream class does not correctly inherit from DessertItem or define the required attributes.
- 💡 What syntax is used to inherit from a parent class and define new attributes?

**Sundae inherits IceCream and defines topping_name & topping_price**: The Sundae class does not correctly inherit from IceCream or define the required attributes.
- 💡 What syntax is used to inherit from a parent class and define new attributes?

**Next step:** Start from the assignment instructions to define the class hierarchy.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessert_item`, `candy`, `cookie`, `icecream`, `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 5 identical items cut to 1, and the 'class attribute' hint was wrong (name is an instance attribute). Placeholder: say so plainly and point to the instructions.

status: todo

```json
{
  "summary": "Your dessert.py is still a placeholder, so there are no classes for the tests to check yet.",
  "items": [
    {
      "test_key": "dessert_item",
      "what_went_wrong": "The tests could not find a DessertItem class, and every other dessert class is built on it.",
      "hint": "Which class does the assignment ask for first, and which classes inherit from it?"
    }
  ],
  "next_step": "Start from the assignment instructions: write DessertItem first, then add one subclass at a time and rerun the tests as you go."
}
```
