<!-- p2-review | case=p2_ds9_sorted_discarded | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_sorted_discarded

**Dessert Shop 9: Sort Receipt Items** · `cascading_failure` · Order.sort calls sorted() and throws the result away

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -156,5 +156,5 @@
 
     def sort(self) -> None:
-        self.order.sort()
+        sorted(self.order)
 
     def order_cost(self) -> float:
```

## What the grader reported

- `order_sort` (Order.sort() sorts items in ascending order based on calculate_cost()): `E     Use -v to get more diff`
- `student_sort_tests` (Student test suite includes test cases validating relational comparison operators and Order.sort()): `E   FAIL...`
- Passing: DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost, DS8 payment interface, packaging protocols, and class hierarchy intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your relational operators are correctly implemented, but the sorting logic is not producing the expected order.

**Order.sort() sorts items in ascending order based on calculate_cost()**: The items in the order are not sorted in the correct ascending order based on their calculated costs.
- 💡 How is the list being modified or returned within the Order.sort() method?

**Next step:** Review the Order.sort() method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_sort`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Kept the good hint and added a concrete way to see it. sort() is cut off from the prompt.

> Updated after 4159d52 (Claude): The student's own sort test now fails too, and Order.sort is visible to the model under prompt v5. Added a follow-on item.

status: todo

```json
{
  "summary": "Your relational operators are correct, but calling sort() does not change the order, and your own sort test catches it.",
  "items": [
    {
      "test_key": "order_sort",
      "what_went_wrong": "After order.sort(), the items are still in the order they were added.",
      "hint": "How is the list being modified or returned inside Order.sort()? Can you print order.order right after calling it?"
    },
    {
      "test_key": "student_sort_tests",
      "what_went_wrong": "Your test_order_sort fails for the same reason.",
      "hint": "This follows from Order.sort. Fix the method, not the test."
    }
  ],
  "next_step": "Review the Order.sort() method in dessert.py."
}
```
