<!-- p2-review | case=p4_round_ds4_sundae_topping_whole_dollars | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds4_sundae_topping_whole_dollars

**Dessert Shop 4: Abstraction** · `cascading_failure` · Sundae rounds the topping to whole dollars

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -53,5 +53,5 @@
     def calculate_cost(self) -> float:
         base_cost = super().calculate_cost()
-        return round(base_cost + self.topping_price, 2)
+        return round(base_cost, 2) + round(self.topping_price)
```

## What the grader reported

- `calculate_cost` (calculate_cost() computes price per weight, dozen, and scoops for subclasses): `E     Expected: 3.36 ± 3.4e-06`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 7.98 ± 8.0e-06`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_tax() computes tax based on item cost and tax_percent

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your implementation of the dessert cost calculations is producing incorrect totals.

**calculate_cost() computes price per weight, dozen, and scoops for subclasses**: The cost calculation for the Sundae class is not correctly combining the base ice cream cost and the topping price.
- 💡 How does the current calculation handle the rounding of the base cost before adding the topping price?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order cost is lower than expected due to cumulative rounding errors.
- 💡 Should you be rounding the individual item costs before summing them in the order total?

**Next step:** Review the rounding logic in the Sundae and Order classes.

Automatic checks on the draft: **FAIL** -- 86 words; targets stay at 65 or fewer (the prompt's limit is 80, and the model writes longer than its targets)

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_cost`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Lower direction verified; the summary lists all three passing labels; the hint targets the topping's existing rounding with no value given.

status: approved

```json
{
  "summary": "Your abstract class, default tax rate, and tax calculation work, but Sundae costs come out too low.",
  "items": [
    {
      "test_key": "calculate_cost",
      "what_went_wrong": "A Sundae's cost is lower than the test expects.",
      "hint": "In Sundae.calculate_cost, how precisely is the topping's price rounded?"
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order cost is low as a result.",
      "hint": "Fix Sundae.calculate_cost first."
    }
  ],
  "next_step": "Review Sundae.calculate_cost in dessert.py."
}
```
