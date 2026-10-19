<!-- p2-review | case=p4_round_ds4_tax_floor_division | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds4_tax_floor_division

**Dessert Shop 4: Abstraction** · `cascading_failure` · tax uses floor division, so the rate becomes 0

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(self.calculate_cost() * (self.tax_percent // 100), 2)
```

## What the grader reported

- `tax_percent` (DessertItem tax_percent attribute defaults to 7.25%): `E     Expected: 0.1 ± 1.0e-07`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.03 ± 3.0e-08`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your implementation of the tax calculation logic is currently resulting in zero values.

**DessertItem tax_percent attribute defaults to 7.25%**: The tax calculation is not correctly using the tax percentage attribute.
- 💡 How does the floor division operator affect the result of a division between a small float and a large integer?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax amount is being calculated as zero.
- 💡 Consider using a different arithmetic operator to ensure the percentage is applied correctly to the cost.

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total order tax is summing to zero.
- 💡 This follows from the issue in the individual item tax calculation.

**Next step:** Review the arithmetic operators used in the calculate_tax method.

Automatic checks on the draft: **FAIL** -- 96 words; targets stay at 65 or fewer (the prompt's limit is 80, and the model writes longer than its targets); 96 words with three items; keep follow-on items brief (55 or fewer, the model writes longer than its targets)

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `tax_percent`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): All obtained taxes are zero, so 'no tax is ever charged' is accurate; operator not named. Clarified item 2. Gate ok.

status: approved

```json
{
  "summary": "Your abstract class and cost calculations work, but no tax is ever charged.",
  "items": [
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Item taxes are far lower than expected.",
      "hint": "In calculate_tax, what does your percent-to-rate conversion actually produce?"
    },
    {
      "test_key": "tax_percent",
      "what_went_wrong": "The tax with a changed rate is low too.",
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
