<!-- p2-review | case=p4b_round_ds4_tax_one_place | drafted_by=claude-preedit | prompt=v9 -->
# p4b_round_ds4_tax_one_place

**Dessert Shop 4: Abstraction** · `cascading_failure` · tax rounded to one decimal place

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(self.calculate_cost() * (self.tax_percent / 100), 1)
```

## What the grader reported

- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.03 ± 3.0e-08`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), DessertItem tax_percent attribute defaults to 7.25%, calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `claude-preedit` (prompt v9), as the student would see it

Your abstract class, default tax rate, and cost calculations work, but item and order taxes come out too low.

**calculate_tax() computes tax based on item cost and tax_percent**: Item taxes lose too much precision, so small taxes come out low.
- 💡 How precisely does calculate_tax round the tax it returns?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The order tax is low as a result.
- 💡 Fix calculate_tax first.

**Next step:** Review the rounding in DessertItem.calculate_tax.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4b (Claude): Tax rounded too coarsely; checked that both reported values are low. Hint asks how precisely it rounds, never the digit count. Gate ok, 56 words.

status: approved

```json
{
  "summary": "Your abstract class, default tax rate, and cost calculations work, but item and order taxes come out too low.",
  "items": [
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Item taxes lose too much precision, so small taxes come out low.",
      "hint": "How precisely does calculate_tax round the tax it returns?"
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "The order tax is low as a result.",
      "hint": "Fix calculate_tax first."
    }
  ],
  "next_step": "Review the rounding in DessertItem.calculate_tax."
}
```
