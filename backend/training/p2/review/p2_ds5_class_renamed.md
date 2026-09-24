<!-- p2-review | case=p2_ds5_class_renamed | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds5_class_renamed

**Dessert Shop 5: Console Application** · `cascading_failure` · class renamed Shop but main still builds DessertShop()

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -3,5 +3,5 @@
 
 
-class DessertShop:
+class Shop:
     def user_prompt_candy(self) -> Candy:
         name = input("Enter the candy name: ")
```

## What the grader reported

- `dessertshop_class` (DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)): `E    +    where <function isclass at 0x00000177685BC180> = inspect.isclass`
- Passing: DS4 ABC inheritance, cost calculations, and tax formulas intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your dessert shop logic is well-structured, but there is a naming mismatch in your main class definition.

**DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)**: The test is looking for a class named 'DessertShop', but it cannot find it in your code.
- 💡 Check the name of the class in dessertshop.py; does it match the name required by the assignment?

**Next step:** Review the class name in dessertshop.py to ensure it matches the expected name.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessertshop_class`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the name.

status: accepted

```json
{
  "summary": "Your dessert shop logic is well structured, but the test cannot find the shop class by its required name.",
  "items": [
    {
      "test_key": "dessertshop_class",
      "what_went_wrong": "The test looks for a class named DessertShop and cannot find it.",
      "hint": "Check the name of the class in dessertshop.py. Does it match the name the assignment asks for, and the name main uses?"
    }
  ],
  "next_step": "Review the class name at the top of dessertshop.py."
}
```
