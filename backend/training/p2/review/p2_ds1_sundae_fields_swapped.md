<!-- p2-review | case=p2_ds1_sundae_fields_swapped | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_sundae_fields_swapped

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · Sundae assigns topping_price to topping_name and vice versa

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -28,4 +28,4 @@
     def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
         super().__init__(name, scoop_count, price_per_scoop)
-        self.topping_name = topping_name
-        self.topping_price = topping_price
+        self.topping_name = topping_price
+        self.topping_price = topping_name
```

## What the grader reported

- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E    +  where 0.0 = <dessert.Sundae object at 0x1091a02f0>.topping_name`
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your base classes and initial inheritance structures are working correctly. However, there is an issue with how attributes are assigned in the Sundae class.

**Sundae inherits IceCream and defines topping_name & topping_price**: The topping_name attribute is being assigned a numeric value instead of a string.
- 💡 Take a look at the assignments inside the Sundae __init__ method; are the variables being assigned to the correct attributes?

**Next step:** Review the __init__ method of the Sundae class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your base classes and initial inheritance structures are working correctly. However, there is an issue with how attributes are assigned in the Sundae class.",
  "items": [
    {
      "test_key": "sundae",
      "what_went_wrong": "The topping_name attribute is being assigned a numeric value instead of a string.",
      "hint": "Take a look at the assignments inside the Sundae __init__ method. Are the variables being assigned to the correct attributes?"
    }
  ],
  "next_step": "Review the __init__ method of the Sundae class."
}
```
