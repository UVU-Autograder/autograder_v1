<!-- p2-review | case=p2_ds9_gt_uses_lt | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_gt_uses_lt

**Dessert Shop 9: Sort Receipt Items** · `single_failure` · __gt__ compares with < (copy-paste from __lt__)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -40,5 +40,5 @@
     def __gt__(self, other: "DessertItem") -> bool:
         if isinstance(other, DessertItem):
-            return self.calculate_cost() > other.calculate_cost()
+            return self.calculate_cost() < other.calculate_cost()
         return NotImplemented
```

## What the grader reported

- `relational_ops` (DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost): `E   assert <dessert.Candy object at 0x10b5defd0> > <dessert.Candy object at 0x10b6323c0>`
- Passing: Order.sort() sorts items in ascending order based on calculate_cost(), Student test suite includes test cases validating relational comparison operators and Order.sort(), DS8 payment interface, packaging protocols, and class hierarchy intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the sorting logic and the required class hierarchy, but there is an issue with the relational operators.

**DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost**: The greater-than operator (__gt__) is currently returning the result of a less-than comparison.
- 💡 Look closely at the logic inside your __gt__ method in the DessertItem class. Does the comparison operator match the method name?

**Next step:** Review the __gt__ method in the DessertItem class in dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `relational_ops`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong gave the fix; kept the draft's good hint.

status: todo

```json
{
  "summary": "Your sorting logic and most relational operators work, but one comparison gives the opposite answer.",
  "items": [
    {
      "test_key": "relational_ops",
      "what_went_wrong": "c2 > c1 returned False; the test expects True because c2 costs more.",
      "hint": "Look closely at the comparison inside your __gt__ method. Does the operator match the method name?"
    }
  ],
  "next_step": "Review the __gt__ method in the DessertItem class in dessert.py."
}
```
