<!-- p2-review | case=p2_ds5_prompt_renamed | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds5_prompt_renamed

**Dessert Shop 5: Console Application** · `single_failure` · user_prompt_candy renamed prompt_candy

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -4,5 +4,5 @@
 
 class DessertShop:
-    def user_prompt_candy(self) -> Candy:
+    def prompt_candy(self) -> Candy:
         name = input("Enter the candy name: ")
         if not name.strip():
@@ -146,5 +146,5 @@
                 done = True
             case "1":
-                item = shop.user_prompt_candy()
+                item = shop.prompt_candy()
                 order.add(item)
                 print(f"{item.name} has been added to your order.")
```

## What the grader reported

- `dessertshop_class` (DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)): `E    +  where False = hasattr(<dessertshop.DessertShop object at 0x000001262D2F8D70>, 'user_prompt_candy')`
- Passing: DS4 ABC inheritance, cost calculations, and tax formulas intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the DessertShop class is missing a specific method required by the test suite.

**DessertShop class defines user input methods (user_prompt_candy, user_prompt_cookie, etc.)**: The DessertShop class does not have a method named 'user_prompt_candy'.
- 💡 Check the naming of your first input method in the DessertShop class; does it match the requirement exactly?

**Next step:** Review the method names required for the DessertShop class in your assignment instructions.

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
  "summary": "Your DessertShop class is mostly in place, but the test cannot find one of its required methods.",
  "items": [
    {
      "test_key": "dessertshop_class",
      "what_went_wrong": "DessertShop has no method named user_prompt_candy.",
      "hint": "Check the name of your candy input method in the DessertShop class. Does it match the requirement exactly?"
    }
  ],
  "next_step": "Review the method names required for the DessertShop class in the assignment instructions."
}
```
