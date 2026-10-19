<!-- p2-review | case=p4_round_ds5_icecream_truncates | drafted_by=gemma4-12b-qat | prompt=v9 -->
# p4_round_ds5_icecream_truncates

**Dessert Shop 5: Console Application** · `cascading_failure` · ice cream cost truncated to whole cents instead of rounded

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -42,5 +42,5 @@
 
     def calculate_cost(self) -> float:
-        return round(self.scoop_count * self.price_per_scoop, 2)
+        return int(self.scoop_count * self.price_per_scoop * 10) / 10
```

## What the grader reported

- `ds4_regression` (DS4 ABC inheritance, cost calculations, and tax formulas intact): `E     Expected: 1.58 ± 1.6e-06`
- Passing: DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)

## Draft by `gemma4-12b-qat` (prompt v9), as the student would see it

Your code successfully implements the required user input methods for the DessertShop class.

**DS4 ABC inheritance, cost calculations, and tax formulas intact**: The cost calculation for the IceCream class is not producing the expected result.
- 💡 How does the current calculation in IceCream compare to the logic required for the other dessert types?

**Next step:** Review the calculate_cost method in the IceCream class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `ds4_regression`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, the exact attribute or parameter to change, or an either/or with the answer in it is not.
- No values from the test results: not the student's value, not the expected one (the student already sees both). Describe the difference in words.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, one sentence per field, under 80 words (at most 15 in `next_step`).
- all-pass cases keep `"items": []`.

> p4 pre-edit (Claude): Slightly-low direction verified; the code truncates rather than rounds, so 'shorten' correctly avoids naming the operator to use.

status: approved

```json
{
  "summary": "Your DessertShop input methods work, but the IceCream cost comes out low.",
  "items": [
    {
      "test_key": "ds4_regression",
      "what_went_wrong": "An IceCream's cost is a little lower than the regression test expects.",
      "hint": "How does IceCream.calculate_cost shorten its result before returning it?"
    }
  ],
  "next_step": "Review IceCream.calculate_cost in dessert.py."
}
```
