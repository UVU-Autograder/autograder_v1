<!-- p2-review | case=p2_ds9_sort_descending | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds9_sort_descending

**Dessert Shop 9: Sort Receipt Items** · `cascading_failure` · Order.sort sorts in reverse

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -156,5 +156,5 @@
 
     def sort(self) -> None:
-        self.order.sort()
+        self.order.sort(reverse=True)
 
     def order_cost(self) -> float:
```

## What the grader reported

- `order_sort` (Order.sort() sorts items in ascending order based on calculate_cost()): `E     Use -v to get more diff`
- Passing: DessertItem defines all 6 relational operators (__eq__, __ne__, __lt__, __gt__, __le__, __ge__) comparing cost, Student test suite includes test cases validating relational comparison operators and Order.sort(), DS8 payment interface, packaging protocols, and class hierarchy intact
- **The changed lines are cut off by the prompt's code budget: the model sees the failure, not the code.** Good feedback here reasons from the assertion alone.

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the relational operators and the sorting logic is correct, but the final order of items does not match the expected sequence.

**Order.sort() sorts items in ascending order based on calculate_cost()**: The list of items in the order is not in the correct ascending order based on their calculated costs.
- 💡 Does your sort method correctly use the cost-based comparison operators you defined?

**Next step:** Review the Order.sort() method in dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_sort`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint pointed at the comparison operators, which work. sort() is cut off from the prompt, so the hint asks the student to print the costs and see the direction.

> Stale after 4159d52 (tightened tests): the grader now reports different failing items: order_sort, student_sort_tests. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your relational operators work, but after sort() the items are not in the order the test expects.",
  "items": [
    {
      "test_key": "order_sort",
      "what_went_wrong": "After order.sort(), the first item is not the cheapest one.",
      "hint": "Can you print the cost of each item after calling sort() and compare it with the ascending order the test expects? Which direction are they going?"
    }
  ],
  "next_step": "Review the Order.sort() method in dessert.py."
}
```
