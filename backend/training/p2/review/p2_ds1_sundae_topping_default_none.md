<!-- p2-review | case=p2_ds1_sundae_topping_default_none | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_sundae_topping_default_none

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · topping_price defaults to None instead of 0.0

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -26,5 +26,5 @@
 
 class Sundae(IceCream):
-    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
+    def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = None):
         super().__init__(name, scoop_count, price_per_scoop)
         self.topping_name = topping_name
```

## What the grader reported

- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E    +  where None = <dessert.Sundae object at 0x1096702f0>.topping_price`
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the base classes and initial inheritance levels is correct. However, there is an issue with the default value for a specific attribute in the Sundae class.

**Sundae inherits IceCream and defines topping_name & topping_price**: The topping_price attribute is returning None instead of the required default value of 0.0.
- 💡 What default value should be assigned to topping_price in the Sundae constructor's parameters?

**Next step:** Review the Sundae class constructor signature.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

status: accepted

```json
{
  "summary": "Your implementation of the base classes and initial inheritance levels is correct. However, there is an issue with the default value for a specific attribute in the Sundae class.",
  "items": [
    {
      "test_key": "sundae",
      "what_went_wrong": "The topping_price attribute is returning None instead of the required default value of 0.0.",
      "hint": "What default value should be assigned to topping_price in the Sundae constructor's parameters?"
    }
  ],
  "next_step": "Review the Sundae class constructor signature."
}
```
