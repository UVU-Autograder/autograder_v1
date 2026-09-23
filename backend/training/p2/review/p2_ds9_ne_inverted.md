<!-- p2-review | case=p2_ds9_ne_inverted | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_ne_inverted

**Dessert Shop 9: Sort Receipt Items** · `single_failure` · __ne__ returns self == other

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -31,5 +31,5 @@
 
     def __ne__(self, other: object) -> bool:
-        return not (self == other)
+        return self == other
 
     def __lt__(self, other: "DessertItem") -> bool:
```

## What the grader reported

- `relational_ops` (DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost): `E   assert <dessert.Candy object at 0x10baca3c0> != <dessert.Candy object at 0x10ba76fd0>`
- Passing: Order.sort() sorts items in ascending order based on calculate_cost(), Student test suite includes test cases validating relational comparison operators and Order.sort(), DS8 payment interface, packaging protocols, and class hierarchy intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the relational operators is working correctly for most cases, but there is an issue with how inequality is handled.

**DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost**: The inequality operator (__ne__) is currently returning the result of the equality operator (__eq__), which causes it to fail when two items are not equal.
- 💡 How should the logic of the 'not equal' operator differ from the 'equal' operator?

**Next step:** Review the logic in the __ne__ method within the DessertItem class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `relational_ops`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong gave the fix. Now describes the result and asks the student to trace __ne__.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your relational operators work for most cases, but != gives the wrong answer.",
  "items": [
    {
      "test_key": "relational_ops",
      "what_went_wrong": "c1 != c2 returned False for two items with different costs.",
      "hint": "What should != return when == is False? Can you trace your __ne__ for these two items?"
    }
  ],
  "next_step": "Review the __ne__ method in the DessertItem class."
}
```
