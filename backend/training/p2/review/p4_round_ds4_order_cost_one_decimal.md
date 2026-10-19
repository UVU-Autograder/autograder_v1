<!-- p2-review | case=p4_round_ds4_order_cost_one_decimal | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds4_order_cost_one_decimal

**Dessert Shop 4: Abstraction** · `single_failure` · order cost rounded to one decimal place

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -79,5 +79,5 @@
 
     def order_cost(self) -> float:
-        return round(sum(item.calculate_cost() for item in self.order), 2)
+        return round(sum(item.calculate_cost() for item in self.order), 1)
 
     def order_tax(self) -> float:
```

## What the grader reported

- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses, calculate_tax() computes tax based on item cost and tax_percent

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your implementation of the order totals is currently producing an incorrect sum.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total cost calculation is rounding to the wrong number of decimal places.
- 💡 How does the precision in your order_cost method affect the final sum?

**Next step:** Review the rounding logic in the order_cost method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Correct method, direction correct (higher), and the ndigits change is not named. Gate ok.

status: approved

```json
{
  "summary": "Your abstract class, tax rate, item costs, and item taxes work, but the order's total cost is slightly off.",
  "items": [
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost comes out slightly higher than the test expects.",
      "hint": "How does order_cost round the total of the item costs?"
    }
  ],
  "next_step": "Review Order.order_cost in dessert.py."
}
```
