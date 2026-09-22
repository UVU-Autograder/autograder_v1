<!-- p2-review | case=p2_ds5_crash_on_bad_number | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds5_crash_on_bad_number

**Dessert Shop 5: Console Application** · `single_failure` · candy weight input not wrapped in try/except, so 'abc' crashes the program

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -9,13 +9,5 @@
             raise ValueError("Name cannot be empty.")
 
-        while True:
-            try:
-                weight = float(input("Enter candy weight(lbs): "))
-                if weight <= 0:
-                    print("Weight must be greater than 0.")
-                    continue
-                break
-            except ValueError:
-                print("Invalid input. Please enter a number value.")
+        weight = float(input("Enter candy weight(lbs): "))
 
         while True:
```

## What the grader reported

- `dessertshop_class` (DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)): `E    +  where -0.5 = <dessert.Candy object at 0x1094cad50>.candy_weight`
- Passing: DS4 ABC inheritance, cost calculations, and tax formulas intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the ABC inheritance and cost calculations, but there is an issue with how candy weight is being handled in the input methods.

**DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)**: The candy weight value is being recorded as -0.5 instead of the expected 0.25.
- 💡 In your user_prompt_candy method, how are you capturing and assigning the weight from the user input?

**Next step:** Review the user_prompt_candy method in dessertshop.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessertshop_class`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Clearer description: -0.5 was accepted where the prompt should keep asking. The hint compares the weight code with the price loop that works.

status: todo

```json
{
  "summary": "Your inheritance and cost logic work, and most of the input checks do too. The candy weight prompt accepts a value it should reject.",
  "items": [
    {
      "test_key": "dessertshop_class",
      "what_went_wrong": "Given a weight of -0.5, your prompt kept it; the test expected the prompt to ask again and end up with 0.25.",
      "hint": "Can you compare how user_prompt_candy reads the weight with how it reads the price? What does the price code do that the weight code does not?"
    }
  ],
  "next_step": "Review the weight input in user_prompt_candy in dessertshop.py."
}
```
