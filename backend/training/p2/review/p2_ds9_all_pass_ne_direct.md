<!-- p2-review | case=p2_ds9_all_pass_ne_direct | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_all_pass_ne_direct

**Dessert Shop 9: Sort Receipt Items** · `all_pass` · valid alternative: __ne__ compares costs directly

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -31,5 +31,7 @@
 
     def __ne__(self, other: object) -> bool:
-        return not (self == other)
+        if isinstance(other, DessertItem):
+            return self.calculate_cost() != other.calculate_cost()
+        return True
 
     def __lt__(self, other: "DessertItem") -> bool:
```

## What the grader reported

- All automated checks passed.
- Passing: DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost, Order.sort() sorts items in ascending order based on calculate_cost(), Student test suite includes test cases validating relational comparison operators and Order.sort(), DS8 payment interface, packaging protocols, and class hierarchy intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission passed all the automated tests.

**Next step:** You could consider extending this work by exploring how to implement a custom sorting algorithm or adding more complex dessert types with unique pricing logic.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Generic extension replaced with one about the student's own choice (__ne__ repeats the comparison instead of reusing __eq__).

status: todo

```json
{
  "summary": "Congratulations! Every test passes, including sorting.",
  "items": [],
  "next_step": "Your __ne__ repeats the cost comparison instead of reusing __eq__. Can you think of what would happen if you later changed how __eq__ compares items?"
}
```
