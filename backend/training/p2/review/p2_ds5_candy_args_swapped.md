<!-- p2-review | case=p2_ds5_candy_args_swapped | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds5_candy_args_swapped

**Dessert Shop 5: Console Application** · `single_failure` · user_prompt_candy builds Candy(name, price, weight)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -29,5 +29,5 @@
                 print("Invalid input. Please enter a number value.")
 
-        return Candy(name, weight, price)
+        return Candy(name, price, weight)
 
     def user_prompt_cookie(self) -> Cookie:
```

## What the grader reported

- `dessertshop_class` (DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)): `E    +  where 0.35 = <dessert.Candy object at 0x108d42c10>.candy_weight`
- Passing: DS4 ABC inheritance, cost calculations, and tax formulas intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the core inheritance and cost calculation logic, but there is an issue with how the Candy object is being instantiated.

**DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)**: The Candy object was created with a weight of 0.35, but the test expected 0.25.
- 💡 Check the order of arguments in your Candy constructor call within the user_prompt_candy method.

**Next step:** Review the __init__ method of the Candy class in dessert.py to see the expected order of parameters.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessertshop_class`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: the hint is now a question comparing the call with Candy's __init__.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your input prompts and inheritance work, but the Candy that user_prompt_candy builds has its values in the wrong places.",
  "items": [
    {
      "test_key": "dessertshop_class",
      "what_went_wrong": "The Candy was created with a weight of 0.35, but the test entered a weight of 0.25.",
      "hint": "Can you compare the order of the values you pass to Candy(...) in user_prompt_candy with the order Candy's __init__ expects?"
    }
  ],
  "next_step": "Review the return line of user_prompt_candy in dessertshop.py."
}
```
