<!-- p2-review | case=p4_round_ds5_cookie_rounds_early | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds5_cookie_rounds_early

**Dessert Shop 5: Console Application** · `cascading_failure` · cookie cost rounds the dozen fraction before multiplying

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -32,5 +32,5 @@
 
     def calculate_cost(self) -> float:
-        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)
+        return round(self.cookie_quantity / 12, 1) * self.price_per_dozen
```

## What the grader reported

- `ds4_regression` (DS4 ABC inheritance, cost calculations, and tax formulas intact): `E     Expected: 2.0 ± 2.0e-06`
- Passing: DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your code successfully implements the required user input methods for the DessertShop class.

**DS4 ABC inheritance, cost calculations, and tax formulas intact**: The cost calculation for cookies results in a value that is slightly off from the expected amount.
- 💡 How does the order of operations and the precision of the division affect the final result before rounding?

**Next step:** Review the Cookie.calculate_cost method's mathematical logic.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `ds4_regression`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Direction correct (lower). Hint covers what gets rounded and when, without saying which step should round. Gate ok.

status: approved

```json
{
  "summary": "Your user input methods work, but the regression check finds your cookie cost is slightly off.",
  "items": [
    {
      "test_key": "ds4_regression",
      "what_went_wrong": "A cookie's cost comes out slightly lower than the test expects.",
      "hint": "In Cookie.calculate_cost, what exactly gets rounded, and at which step?"
    }
  ],
  "next_step": "Review Cookie.calculate_cost in dessert.py."
}
```
