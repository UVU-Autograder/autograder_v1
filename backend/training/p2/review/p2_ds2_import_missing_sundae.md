<!-- p2-review | case=p2_ds2_import_missing_sundae | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_import_missing_sundae

**Dessert Shop 2: Using Classes in main** · `single_failure` · dessertshop.py forgets to import Sundae (NameError in main)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -1,3 +1,3 @@
-from dessert import Candy, Cookie, IceCream, Order, Sundae
+from dessert import Candy, Cookie, IceCream, Order
```

## What the grader reported

- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E   AssertionError: dessertshop.py execution failed: name 'Sundae' is not defined`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae), Order class defines order list, add() method, and len() support

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy and Order class are correctly implemented, but the main script is encountering a naming error.

**dessertshop.py main() constructs Order items and prints formatted receipt**: The program crashed because it cannot find the definition for the 'Sundae' class when trying to add it to the order.
- 💡 Check your import statement in dessertshop.py; is every class you intend to use included there?

**Next step:** Review the import statements at the top of dessertshop.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to where to look.

status: todo

```json
{
  "summary": "Your class hierarchy and Order class are correctly implemented, but the main script cannot find one of the classes it uses.",
  "items": [
    {
      "test_key": "main_output",
      "what_went_wrong": "The program crashed because it cannot find the Sundae class when adding it to the order.",
      "hint": "Check your import statement in dessertshop.py: is every class you use in main included there?"
    }
  ],
  "next_step": "Review the import statements at the top of dessertshop.py."
}
```
