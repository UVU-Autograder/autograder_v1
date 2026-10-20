<!-- p2-review | case=p4_round_ds4_tax_per_mille | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds4_tax_per_mille

**Dessert Shop 4: Abstraction** · `cascading_failure` · tax divides the percent by 1000

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(self.calculate_cost() * (self.tax_percent / 1000), 2)
```

## What the grader reported

- `tax_percent` (DessertItem tax_percent attribute defaults to 7.25%): `E     Expected: 0.1 ± 1.0e-07`
- `calculate_tax` (calculate_tax() computes tax based on item cost and tax_percent): `E     Expected: 0.03 ± 3.0e-08`
- `order_totals` (Order methods order_cost() and order_tax() aggregate total prices accurately): `E     Expected: 0.57 ± 5.7e-07`
- Passing: DessertItem inherits ABC and defines abstract @abstractmethod calculate_cost(), calculate_cost() computes price per weight, dozen, and scoops for subclasses

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your implementation has some logic errors regarding tax calculations and percentage conversions.

**DessertItem tax_percent attribute defaults to 7.25%**: The tax calculation is using an incorrect divisor for the percentage conversion.
- 💡 How many units are in a whole percentage (e.g., 100%)?

**calculate_tax() computes tax based on item cost and tax_percent**: The tax amount is returning zero because of the previous calculation error.
- 💡 If the percentage math is corrected, will this method then produce the expected tax amount?

**Order methods order_cost() and order_tax() aggregate total prices accurately**: The total tax for the order is incorrect because it relies on the faulty individual tax calculations.
- 💡 Review how the individual tax values are being summed in the Order class.

**Next step:** Review the math inside the calculate_tax method in dessert.py.

Automatic checks on the draft: **FAIL** -- stated a score/grade: '100%'; 100 words; targets stay at 65 or fewer (the prompt's limit is 80, and the model writes longer than its targets); 100 words with three items; keep follow-on items brief (55 or fewer, the model writes longer than its targets); contains what to type (100), found only in the model solution

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `tax_percent`, `calculate_tax`, `order_totals`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Hint points at the percent-to-rate conversion without naming the divisor. Clarified item 2. Gate ok at 55 words.

> p4b (Claude): 43 words; verified lower direction; conversion hint is correct since the diff changes it; divisor never named.

status: approved

```json
{
  "summary": "Your abstract class and cost calculations work, but every tax is too low.",
  "items": [
    {
      "test_key": "calculate_tax",
      "what_went_wrong": "Item taxes are far lower than expected.",
      "hint": "How does calculate_tax turn the tax percentage into a rate?"
    },
    {
      "test_key": "tax_percent",
      "what_went_wrong": "Same cause.",
      "hint": "Fix calculate_tax first."
    },
    {
      "test_key": "order_totals",
      "what_went_wrong": "Same cause.",
      "hint": "Same fix."
    }
  ],
  "next_step": "Review DessertItem.calculate_tax in dessert.py."
}
```
