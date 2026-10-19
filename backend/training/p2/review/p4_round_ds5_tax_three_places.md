<!-- p2-review | case=p4_round_ds5_tax_three_places | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds5_tax_three_places

**Dessert Shop 5: Console Application** · `cascading_failure` · tax rounded to three places

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
     def calculate_tax(self) -> float:
-        return round(self.calculate_cost() * (self.tax_percent / 100), 2)
+        return round(self.calculate_cost() * (self.tax_percent / 100), 3)
```

## What the grader reported

- `ds4_regression` (DS4 ABC inheritance, cost calculations, and tax formulas intact): `E     Expected: 0.52 ± 5.2e-07`
- Passing: DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your code successfully implements the required user input methods for the DessertShop class.

**DS4 ABC inheritance, cost calculations, and tax formulas intact**: The calculated order tax does not match the expected value.
- 💡 How does rounding the tax of each individual item affect the final sum of the total tax?

**Next step:** Review the order_tax method in the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `ds4_regression`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Direction is correct (higher) and next_step points at calculate_tax, where the bug is. Places count not named. Gate ok.

status: approved

```json
{
  "summary": "Your user input methods work, but the regression check finds the order tax slightly off.",
  "items": [
    {
      "test_key": "ds4_regression",
      "what_went_wrong": "The order tax comes out slightly higher than the test expects.",
      "hint": "How does calculate_tax round each item's tax before the order totals them?"
    }
  ],
  "next_step": "Review DessertItem.calculate_tax in dessert.py."
}
```
