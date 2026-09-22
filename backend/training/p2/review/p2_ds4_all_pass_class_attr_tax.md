<!-- p2-review | case=p2_ds4_all_pass_class_attr_tax | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_all_pass_class_attr_tax

**Dessert Shop 4: Abstraction** · `all_pass` · valid alternative: tax_percent as a class attribute

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -3,7 +3,8 @@
 
 class DessertItem(ABC):
+    tax_percent: float = 7.25
+
     def __init__(self, name: str = ""):
         self.name = name
-        self.tax_percent: float = 7.25
 
     @abstractmethod
```

## What the grader reported

- All automated checks passed.
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses, calculate_tax() computes tax based on item cost and tax_percent, Order methods order_cost() and order_tax() aggregate total prices accurately

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your implementation of the Dessert Shop system is complete and passed all automated tests.

**Next step:** You could consider extending this system by adding a 'SpecialOffer' class that applies a discount to the total order cost using operator overloading.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Generic extension replaced with one about the student's own choice (tax_percent as a class attribute).

status: todo

```json
{
  "summary": "Congratulations! All the tests pass.",
  "items": [],
  "next_step": "Your tax_percent is a class attribute, so every dessert shares one value. Can you work out what happens if you change it on one Candy, and whether that is what a real shop would want?"
}
```
