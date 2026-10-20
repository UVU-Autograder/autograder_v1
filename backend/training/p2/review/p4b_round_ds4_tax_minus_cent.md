<!-- p2-review | case=p4b_round_ds4_tax_minus_cent | drafted_by=claude-preedit | prompt=v9 -->
# p4b_round_ds4_tax_minus_cent

**Dessert Shop 4: Abstraction** · `cascading_failure` · tax rounded, then a cent taken off

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(self.calculate_cost() * (self.tax_percent / 100), 2) - 0.01
```

## What the grader reported

- `tax_percent` (DessertItem tax_percent attribute defaults to 7.25%): `E     Expected: 0.1 ± 1.0e-07`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.03 ± 3.0e-08`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `claude-preedit` (prompt v9), as the student would see it

Your abstract class and cost calculations work, but every tax is slightly low.

**calculate_tax() computes tax based on item cost and tax_percent**: Each item's tax runs low.
- 💡 What does calculate_tax do after rounding?

**DessertItem tax_percent attribute defaults to 7.25%**: The changed-rate tax is low too.
- 💡 Same cause.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The order tax is low too.
- 💡 Fix calculate_tax first.

**Next step:** Review DessertItem.calculate_tax in dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `tax_percent`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4b (Claude): Stray term after rounding; checked all three reported values are low. Hint points after rounding, no operator or amount, and never blames the rate. Gate ok, 45 words.

status: approved

```json
{
  "summary": "Your abstract class and cost calculations work, but every tax is slightly low.",
  "items": [
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Each item's tax runs low.",
      "hint": "What does calculate_tax do after rounding?"
    },
    {
      "test_key": "tax_percent",
      "what_went_wrong": "The changed-rate tax is low too.",
      "hint": "Same cause."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order tax is low too.",
      "hint": "Fix calculate_tax first."
    }
  ],
  "next_step": "Review DessertItem.calculate_tax in dessert.py."
}
```
