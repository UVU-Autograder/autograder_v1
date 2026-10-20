<!-- p2-review | case=p4b_round_ds4_tax_extra_factor | drafted_by=claude-preedit | prompt=v9 -->
# p4b_round_ds4_tax_extra_factor

**Dessert Shop 4: Abstraction** · `cascading_failure` · tax multiplied by a stray extra factor

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(self.calculate_cost() * (self.tax_percent / 100) * 1.1, 2)
```

## What the grader reported

- `tax_percent` (DessertItem tax_percent attribute defaults to 7.25%): `E     Expected: 0.1 ± 1.0e-07`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.14 ± 1.4e-07`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `claude-preedit` (prompt v9), as the student would see it

Your abstract class and cost calculations work, but taxes run high.

**calculate_tax() computes tax based on item cost and tax_percent**: Item taxes run high.
- 💡 Besides cost and rate, what else does calculate_tax use?

**DessertItem tax_percent attribute defaults to 7.25%**: The changed-rate tax is high too.
- 💡 Same cause.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The order tax is high too.
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

> p4b (Claude): Stray extra factor; checked all reported values are high. Rate is mentioned only as a landmark, not blamed, and no operator is named. Gate ok, 45 words.

status: approved

```json
{
  "summary": "Your abstract class and cost calculations work, but taxes run high.",
  "items": [
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Item taxes run high.",
      "hint": "Besides cost and rate, what else does calculate_tax use?"
    },
    {
      "test_key": "tax_percent",
      "what_went_wrong": "The changed-rate tax is high too.",
      "hint": "Same cause."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order tax is high too.",
      "hint": "Fix calculate_tax first."
    }
  ],
  "next_step": "Review DessertItem.calculate_tax in dessert.py."
}
```
