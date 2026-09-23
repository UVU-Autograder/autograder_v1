<!-- p2-review | case=p2_ds1_two_bugs | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_two_bugs

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · two independent bugs: Candy stores weight, and Sundae passes only name to super

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -7,5 +7,5 @@
     def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
         super().__init__(name)
-        self.candy_weight = candy_weight
+        self.weight = candy_weight
         self.price_per_pound = price_per_pound
 
@@ -27,5 +27,5 @@
 class Sundae(IceCream):
     def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
-        super().__init__(name, scoop_count, price_per_scoop)
+        super().__init__(name)
         self.topping_name = topping_name
         self.topping_price = topping_price
```

## What the grader reported

- `candy` (Candy inherits DessertItem and defines candy_weight & price_per_pound): `E   AttributeError: 'Candy' object has no attribute 'candy_weight'`
- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E    +  where 0 = <dessert.Sundae object at 0x1090d1d10>.scoop_count`
- Passing: DessertItem base class defines name attribute with default '', Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the base classes and Cookie class is working correctly, but there are issues with attribute naming and inheritance in the Candy and Sundae classes.

**Candy inherits DessertItem and defines candy_weight & price_per_pound**: The Candy class is missing the specific attribute name required by the test.
- 💡 What is the exact name of the weight attribute expected by the requirements?

**Sundae inherits IceCream and defines topping_name & topping_price**: The scoop_count attribute is not being updated correctly when a Sundae object is created.
- 💡 How does the Sundae constructor pass its arguments to the IceCream constructor?

**Next step:** Review the requirements for the Candy class attributes and the super() call in the Sundae class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `candy`, `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your implementation of the base classes and Cookie class is working correctly, but there are issues with attribute naming and inheritance in the Candy and Sundae classes.",
  "items": [
    {
      "test_key": "candy",
      "what_went_wrong": "The Candy class is missing the specific attribute name required by the test.",
      "hint": "What is the exact name of the weight attribute expected by the requirements?"
    },
    {
      "test_key": "sundae",
      "what_went_wrong": "The scoop_count attribute is not being updated correctly when a Sundae object is created.",
      "hint": "How does the Sundae constructor pass its arguments to the IceCream constructor?"
    }
  ],
  "next_step": "Review the requirements for the Candy class attributes and the super() call in the Sundae class."
}
```
