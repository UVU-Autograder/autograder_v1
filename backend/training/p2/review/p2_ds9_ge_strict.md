<!-- p2-review | case=p2_ds9_ge_strict | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_ge_strict

**Dessert Shop 9: Sort Receipt Items** · `single_failure` · __ge__ uses > so equal costs compare False

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -50,5 +50,5 @@
     def __ge__(self, other: "DessertItem") -> bool:
         if isinstance(other, DessertItem):
-            return self.calculate_cost() >= other.calculate_cost()
+            return self.calculate_cost() > other.calculate_cost()
         return NotImplemented
```

## What the grader reported

- `relational_ops` (DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost): `E   assert <dessert.Candy object at 0x10b6e63c0> >= <dessert.Candy object at 0x10b697110>`
- Passing: Order.sort() sorts items in ascending order based on calculate_cost(), Student test suite includes test cases validating relational comparison operators and Order.sort(), DS8 payment interface, packaging protocols, and class hierarchy intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the relational operators for DessertItem is mostly correct, but there is a logic error in one of the comparison methods.

**DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost**: The greater-than-or-equal-to operator (__ge__) is currently using the greater-than logic instead of the greater-than-or-equal-to logic.
- 💡 Compare the logic inside your __ge__ method with your __gt__ method; should they be identical?

**Next step:** Review the __ge__ method in the DessertItem class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `relational_ops`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong and the hint gave the fix. Now describes the equal-cost case and asks what >= should return there.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Most of your relational operators work, and sorting does too. One comparison is wrong when two items cost the same.",
  "items": [
    {
      "test_key": "relational_ops",
      "what_went_wrong": "c1 >= c3 returned False, but these two items cost the same, so the test expects True.",
      "hint": "What should >= return when two items cost exactly the same? Can you check what your __ge__ returns in that case?"
    }
  ],
  "next_step": "Review the __ge__ method in the DessertItem class."
}
```
