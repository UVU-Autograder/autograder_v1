<!-- p2-review | case=p2_ds1_all_pass_explicit_parent | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_all_pass_explicit_parent

**Dessert Shop 1: Inheritance Superclass** · `all_pass` · valid alternative: Candy calls DessertItem.__init__(self, name) instead of super()

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -6,5 +6,5 @@
 class Candy(DessertItem):
     def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0):
-        super().__init__(name)
+        DessertItem.__init__(self, name)
         self.candy_weight = candy_weight
         self.price_per_pound = price_per_pound
```

## What the grader reported

- All automated checks passed.
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop, Sundae inherits IceCream and defines topping_name & topping_price

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Great job! Your implementation of the dessert hierarchy and inheritance structure is correct.

**Next step:** Consider how you might use operator overloading to compare the prices of different dessert types.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

status: approved

```json
{
  "summary": "Great job! Every class in your dessert hierarchy is set up correctly and all the tests pass.",
  "items": [],
  "next_step": "Your Candy class calls DessertItem.__init__ directly while the others use super(). Both work here. Look up what super() does differently and when that difference would matter."
}
```
