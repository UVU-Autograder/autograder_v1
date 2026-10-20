<!-- p2-review | case=p4b_round_ds4_tax_rounds_cost_first | drafted_by=claude-preedit | prompt=v9 -->
# p4b_round_ds4_tax_rounds_cost_first

**Dessert Shop 4: Abstraction** · `cascading_failure` · cost rounded to one decimal before the tax is taken

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(round(self.calculate_cost(), 1) * (self.tax_percent / 100), 2)
```

## What the grader reported

- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.11 ± 1.1e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `claude-preedit` (prompt v9), as the student would see it

Your abstract class, default tax rate, and cost calculations work, but some taxes come out slightly high.

**calculate_tax() computes tax based on item cost and tax_percent**: Some item taxes differ slightly from what the cost and rate should give.
- 💡 In calculate_tax, what happens to the cost before it meets the rate?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The order tax is slightly high as a result.
- 💡 Fix calculate_tax first.

**Next step:** Review how DessertItem.calculate_tax uses the cost.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4b (Claude): Cost is rounded too early; checked that the reported values run high. Hint asks what happens to the cost first, without stating the fix. Gate ok, 60 words.

status: approved

```json
{
  "summary": "Your abstract class, default tax rate, and cost calculations work, but some taxes come out slightly high.",
  "items": [
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Some item taxes differ slightly from what the cost and rate should give.",
      "hint": "In calculate_tax, what happens to the cost before it meets the rate?"
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order tax is slightly high as a result.",
      "hint": "Fix calculate_tax first."
    }
  ],
  "next_step": "Review how DessertItem.calculate_tax uses the cost."
}
```
