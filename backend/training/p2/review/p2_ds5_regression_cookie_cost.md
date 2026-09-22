<!-- p2-review | case=p2_ds5_regression_cookie_cost | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds5_regression_cookie_cost

**Dessert Shop 5: Console Application** · `single_failure` · Cookie cost uses price per cookie (DS4 regression)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -32,5 +32,5 @@
 
     def calculate_cost(self) -> float:
-        return round((self.cookie_quantity / 12) * self.price_per_dozen, 2)
+        return round(self.cookie_quantity * self.price_per_dozen, 2)
```

## What the grader reported

- `ds4_regression` (DS4 ABC inheritance, cost calculations, and tax formulas intact): `E     Expected: 2.0 ± 2.0e-06`
- Passing: DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the required user input methods for the DessertShop class. However, there is a calculation error in the cookie cost logic.

**DS4 ABC inheritance, cost calculations, and tax formulas intact**: The calculated cost for the cookies is 23.94, but the test expected 2.00.
- 💡 How does the price per dozen relate to the quantity of cookies provided in the input?

**Next step:** Review the Cookie.calculate_cost method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `ds4_regression`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: says this is a Dessert Shop 4 behavior that broke.

status: todo

```json
{
  "summary": "Your new DessertShop input methods work. One cost calculation from Dessert Shop 4 has broken.",
  "items": [
    {
      "test_key": "ds4_regression",
      "what_went_wrong": "A Cookie costs 23.94; the Dessert Shop 4 test expects 2.00.",
      "hint": "How does the price per dozen relate to the number of cookies in the order? Can you work out 6 cookies by hand?"
    }
  ],
  "next_step": "Review the Cookie.calculate_cost method in dessert.py."
}
```
