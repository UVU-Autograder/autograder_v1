<!-- p2-review | case=p2_ds1_icecream_attr_typo | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_icecream_attr_typo

**Dessert Shop 1: Inheritance Superclass** · `cascading_failure` · IceCream stores scoops_count instead of scoop_count (Sundae inherits the typo)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -21,5 +21,5 @@
     def __init__(self, name: str = "", scoop_count: int = 0, price_per_scoop: float = 0.0):
         super().__init__(name)
-        self.scoop_count = scoop_count
+        self.scoops_count = scoop_count
         self.price_per_scoop = price_per_scoop
```

## What the grader reported

- `icecream` (IceCream inherits DessertItem and defines scoop_count & price_per_scoop): `E   AttributeError: 'IceCream' object has no attribute 'scoop_count'. Did you mean: 'scoops_count'?`
- `sundae` (Sundae inherits IceCream and defines topping_name & topping_price): `E   AttributeError: 'Sundae' object has no attribute 'scoop_count'. Did you mean: 'scoops_count'?`
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the base classes and Candy and Cookie classes is correct. However, there is an issue with the attribute names in the IceCream and Sundae classes.

**IceCream inherits DessertItem and defines scoop_count & price_per_scoop**: The IceCream class is missing the attribute 'scoop_count'.
- 💡 How does the variable name you defined in the __init__ method compare to the name expected by the test?

**Sundae inherits IceCream and defines topping_name & topping_price**: The Sundae class is missing the attribute 'scoop_count'.
- 💡 Since Sundae inherits from IceCream, how does the naming in the parent class affect the child class?

**Next step:** Review the attribute names in the IceCream class definition.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `icecream`, `sundae`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

status: accepted

```json
{
  "summary": "Your implementation of the base classes and Candy and Cookie classes is correct. However, there is an issue with the attribute names in the IceCream and Sundae classes.",
  "items": [
    {
      "test_key": "icecream",
      "what_went_wrong": "The IceCream class is missing the attribute 'scoop_count'.",
      "hint": "How does the variable name you defined in the __init__ method compare to the name expected in testing?"
    },
    {
      "test_key": "sundae",
      "what_went_wrong": "The Sundae class is missing the attribute 'scoop_count'.",
      "hint": "Since Sundae inherits from IceCream, how does the naming in the parent class affect the child class?"
    }
  ],
  "next_step": "Review the attribute names in the IceCream class definition."
}
```
