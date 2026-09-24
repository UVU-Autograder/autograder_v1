<!-- p2-review | case=p2_ds10_import_missing | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_import_missing

**Dessert Shop 10: Combine Like Items** · `cascading_failure` · dessert.py never imports Combinable (NameError at import)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -4,5 +4,4 @@
 from typing import Any
 
-from combine import Combinable
 from packaging import Packaging
 from payment import Payable, PayType
```

## What the grader reported

- `candy_combinable` (Candy implements Combinable protocol merging candy_weight for matching items): `E   NameError: name 'Combinable' is not defined`
- `cookie_combinable` (Cookie implements Combinable protocol merging cookie_quantity for matching items): `E   NameError: name 'Combinable' is not defined`
- `order_combine` (Order.add() automatically combines like items when matching item is present): `E   NameError: name 'Combinable' is not defined`
- `ds9_regression` (DS9 Order.sort() and relational comparison operators intact): `E   NameError: name 'Combinable' is not defined`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the Combinable protocol and its integration into the dessert items is working well, but there is a scope issue in your dessert logic.

**Order.add() automatically combines like items when matching item is present**: The code encountered a NameError because it cannot find the definition of 'Combinable' inside the dessert.py file.
- 💡 How can you make the 'Combinable' protocol available to the 'DessertItem' classes in dessert.py?

**Next step:** Check the imports at the top of dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_combine`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint nearly said 'import it'. Now compares with Packaging and Payable, which the file already brings in correctly.

> Updated after 4159d52 (Claude): Now all four tests fail on the same NameError. Cut to 3 items: one root cause, the rest follow.

status: todo

```json
{
  "summary": "Your Combinable protocol and dessert classes are written, but dessert.py cannot find one of the names it uses, so every test stops there.",
  "items": [
    {
      "test_key": "candy_combinable",
      "what_went_wrong": "Loading dessert.py fails with \"name 'Combinable' is not defined\".",
      "hint": "Where does the name Combinable come from? Can you compare it with how Packaging and Payable get into dessert.py?"
    },
    {
      "test_key": "cookie_combinable",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This follows from the missing name. Fix that first."
    },
    {
      "test_key": "order_combine",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This clears once dessert.py can find Combinable."
    }
  ],
  "next_step": "Check the top of dessert.py. The Dessert Shop 9 test fails for the same reason."
}
```
