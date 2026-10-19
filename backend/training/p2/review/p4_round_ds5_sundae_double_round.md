<!-- p2-review | case=p4_round_ds5_sundae_double_round | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds5_sundae_double_round

**Dessert Shop 5: Console Application** · `cascading_failure` · Sundae rounds the base to one decimal before adding the topping

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -53,5 +53,5 @@
     def calculate_cost(self) -> float:
         base_cost = super().calculate_cost()
-        return round(base_cost + self.topping_price, 2)
+        return round(round(base_cost, 1) + self.topping_price, 2)
```

## What the grader reported

- `ds4_regression` (DS4 ABC inheritance, cost calculations, and tax formulas intact): `E     Expected: 3.36 ± 3.4e-06`
- Passing: DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your code successfully implements the required user input methods for the DessertShop class.

**DS4 ABC inheritance, cost calculations, and tax formulas intact**: The calculated cost for the Sundae class does not match the expected value.
- 💡 How does the rounding inside the Sundae.calculate_cost method affect the final sum compared to the base class logic?

**Next step:** Review the rounding logic in the Sundae.calculate_cost method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `ds4_regression`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Slightly-high direction verified; the hint points at the existing inner rounding of the base cost without naming precision or placement.

status: approved

```json
{
  "summary": "Your DessertShop input methods work, but the Sundae cost comes out slightly high.",
  "items": [
    {
      "test_key": "ds4_regression",
      "what_went_wrong": "A Sundae's cost is higher than the regression test expects.",
      "hint": "How does Sundae.calculate_cost round the ice cream part of the price?"
    }
  ],
  "next_step": "Review Sundae.calculate_cost in dessert.py."
}
```
