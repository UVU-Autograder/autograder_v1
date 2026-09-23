<!-- p2-review | case=p2_ds5_cookie_qty_float | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds5_cookie_qty_float

**Dessert Shop 5: Console Application** · `single_failure` · cookie quantity read with float(), so 'abc' check and integer quantities break

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -38,5 +38,5 @@
         while True:
             try:
-                qty = int(input("Enter the quantity of cookies: "))
+                qty = input("Enter the quantity of cookies: ")
                 if qty <= 0:
                     print("Quantity must be greater than 0.")
```

## What the grader reported

- `dessertshop_class` (DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)): `E   TypeError: '<=' not supported between instances of 'str' and 'int'`
- Passing: DS4 ABC inheritance, cost calculations, and tax formulas intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the core inheritance and cost calculation logic, but there is an issue with how user input is processed.

**DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)**: The program is trying to compare a string to an integer during the cookie quantity check.
- 💡 In the user_prompt_cookie method, what type of data is returned by the input() function before it is converted?

**Next step:** Review the user_prompt_cookie method in dessertshop.py to ensure the input is converted to the correct numeric type before comparison.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessertshop_class`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): next_step gave the fix ('convert to the correct numeric type'). Now compares with user_prompt_candy, which does it right.

status: accepted

```json
{
  "summary": "Your inheritance and cost logic work, but the cookie prompt crashes before it can check the quantity.",
  "items": [
    {
      "test_key": "dessertshop_class",
      "what_went_wrong": "The cookie prompt fails with \"'<=' not supported between instances of 'str' and 'int'\".",
      "hint": "In user_prompt_cookie, what type of value does input() give you, and what type is the quantity compared with?"
    }
  ],
  "next_step": "Compare user_prompt_cookie with user_prompt_candy in dessertshop.py."
}
```
