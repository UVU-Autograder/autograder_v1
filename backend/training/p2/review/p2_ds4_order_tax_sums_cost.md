<!-- p2-review | case=p2_ds4_order_tax_sums_cost | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds4_order_tax_sums_cost

**Dessert Shop 4: Abstraction** · `single_failure` · order_tax sums calculate_cost instead of calculate_tax

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -82,3 +82,3 @@
 
     def order_tax(self) -> float:
-        return round(sum(item.calculate_tax() for item in self.order), 2)
+        return round(sum(item.calculate_cost() for item in self.order), 2)
```

## What the grader reported

- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses, calculate_tax() computes tax based on item cost and tax_percent

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the DessertItem hierarchy is correct, but there is an issue with how the Order class calculates the total tax.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The order_tax() method is returning the total cost of all items instead of the sum of the taxes for each item.
- 💡 How does the order_tax() method currently calculate its return value compared to what it should be summing?

**Next step:** Review the order_tax() method in the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong stated the fix; now it gives the numbers (7.98 is the order cost) and asks the student to compare order_tax with order_cost.

status: accepted

```json
{
  "summary": "Your DessertItem hierarchy and order_cost work. The order's total tax is far too high.",
  "items": [
    {
      "test_key": "order_totals",
      "what_went_wrong": "order_tax() returned 7.98, the same as the order's cost; the test expects 0.57.",
      "hint": "Can you compare order_tax with order_cost line by line? What is the one thing that should be different between them?"
    }
  ],
  "next_step": "Review the order_tax method in the Order class."
}
```
