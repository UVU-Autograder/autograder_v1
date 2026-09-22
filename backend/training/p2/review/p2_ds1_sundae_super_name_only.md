<!-- p2-review | case=p2_ds1_sundae_super_name_only | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_sundae_super_name_only

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · Sundae passes only name to IceCream.__init__, so scoops and price stay at defaults

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -27,5 +27,5 @@
 class Sundae(IceCream):
     def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0, topping_name: str = "", topping_price: float = 0.0):
-        super().__init__(name, scoop_count, price_per_scoop)
+        super().__init__(name)
         self.topping_name = topping_name
         self.topping_price = topping_price
```

## What the grader reported

- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E    +  where 0 = <dessert.Sundae object at 0x108af1a90>.scoop_count`
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your base classes and initial inheritance structures are working correctly. However, there is an issue with how the Sundae class handles its inherited attributes.

**Sundae inherits IceCream and defines topping_name & topping_price**: The scoop_count attribute is being set to 0 instead of the expected value.
- 💡 When you call super().__init__ in the Sundae class, which arguments are you passing to the IceCream constructor?

**Next step:** Review the __init__ method of the Sundae class.

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
  "summary": "Your base classes and initial inheritance structures are working correctly. However, there is an issue with how the Sundae class handles its inherited attributes.",
  "items": [
    {
      "test_key": "sundae",
      "what_went_wrong": "The scoop_count attribute is being set to 0 instead of the expected value.",
      "hint": "When you call super().__init__ in the Sundae class, which arguments are you passing to the IceCream constructor?"
    }
  ],
  "next_step": "Review the __init__ method of the Sundae class."
}
```
