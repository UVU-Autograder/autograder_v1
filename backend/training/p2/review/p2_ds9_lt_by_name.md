<!-- p2-review | case=p2_ds9_lt_by_name | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_lt_by_name

**Dessert Shop 9: Sort Receipt Items** · `cascading_failure` · __lt__ compares names alphabetically instead of cost

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -35,5 +35,5 @@
     def __lt__(self, other: "DessertItem") -> bool:
         if isinstance(other, DessertItem):
-            return self.calculate_cost() < other.calculate_cost()
+            return self.name < other.name
         return NotImplemented
```

## What the grader reported

- `order_sort` (Order.sort() sorts items in ascending order based on calculate_cost()): `E     Use -v to get more diff`
- Passing: DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost, Student test suite includes test cases validating relational comparison operators and Order.sort(), DS8 payment interface, packaging protocols, and class hierarchy intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the relational operators is mostly correct, but there is a discrepancy in how items are compared during sorting.

**Order.sort() sorts items in ascending order based on calculate_cost()**: The list of items is not being sorted in the expected ascending order based on cost.
- 💡 Compare the logic in your __lt__ method with your __gt__, __le__, and __ge__ methods. Are they all using the same criteria?

**Next step:** Review the __lt__ method in the DessertItem class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_sort`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: the hint (compare the criteria across operators) is exactly right.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your relational operators are mostly correct, but sorting does not put the items in order of cost.",
  "items": [
    {
      "test_key": "order_sort",
      "what_went_wrong": "After sorting, the items are not in ascending order of cost.",
      "hint": "Compare the logic in your __lt__ method with your __gt__, __le__ and __ge__ methods. Are they all using the same thing to compare?"
    }
  ],
  "next_step": "Review the __lt__ method in the DessertItem class."
}
```
