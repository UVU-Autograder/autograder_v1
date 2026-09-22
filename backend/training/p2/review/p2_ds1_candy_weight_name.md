<!-- p2-review | case=p2_ds1_candy_weight_name | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_candy_weight_name

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · Candy stores weight instead of candy_weight

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
```

## What the grader reported

- `candy` (Candy inherits DessertItem and defines candy_weight & price_per_pound): `E   AttributeError: 'Candy' object has no attribute 'candy_weight'`
- Passing: DessertItem base class defines name attribute with default '', Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop, Sundae inherits IceCream and defines topping_name & topping_price

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the DessertItem base class and most subclasses is working correctly. However, there is an issue with the attribute naming in the Candy class.

**Candy inherits DessertItem and defines candy_weight & price_per_pound**: The test expected to find an attribute named 'candy_weight', but it could not find that specific name on the Candy object.
- 💡 How does the variable name you defined in the Candy class's __init__ method compare to the name required by the assignment?

**Next step:** Review the Candy class definition in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `candy`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

status: accepted

```json
{
  "summary": "Your implementation of the DessertItem base class and most subclasses is working correctly. However, there is an issue with the attribute naming in the Candy class.",
  "items": [
    {
      "test_key": "candy",
      "what_went_wrong": "The test expected to find an attribute named 'candy_weight', but it could not find that specific name on the Candy object.",
      "hint": "How does the variable name you defined in the Candy class's __init__ method compare to the name required by the rubric?"
    }
  ],
  "next_step": "Review the Candy class definition in dessert.py"
}
```
