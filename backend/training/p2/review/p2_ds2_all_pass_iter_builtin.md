<!-- p2-review | case=p2_ds2_all_pass_iter_builtin | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_all_pass_iter_builtin

**Dessert Shop 2: Using Classes in main** · `all_pass` · valid alternative: __iter__ returns iter(self.order)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -44,6 +44,5 @@
 
     def __iter__(self) -> "Order":
-        self._index = 0
-        return self
+        return iter(self.order)
 
     def __next__(self) -> DessertItem:
```

## What the grader reported

- All automated checks passed.
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae), Order class defines order list, add() method, and len() support, dessertshop.py main() constructs Order items and prints formatted receipt

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission passed all the automated tests and follows the required class hierarchy.

**Next step:** Consider how you might use operator overloading to make adding items to an order even more intuitive.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Generic next step replaced with one about the student's own choice (iter(self.order) means __next__ never runs).

status: accepted

```json
{
  "summary": "Great job! Every test passes and your Order class works in a for loop.",
  "items": [],
  "next_step": "Your __iter__ returns the list's own iterator, so your __next__ never runs. Can you work out why the for loop still works, and when writing your own __next__ would be the better choice?"
}
```
