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

- `order_combine` (Order.add() automatically combines like items when matching item is present): `E   NameError: name 'Combinable' is not defined`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Candy implements Combinable protocol merging candy_weight for matching items, Cookie implements Combinable protocol merging cookie_quantity for matching items, DS9 Order.sort() and relational comparison operators intact

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

> Stale after 4159d52 (tightened tests): the grader now reports different failing items: candy_combinable, cookie_combinable, order_combine, ds9_regression. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your Combinable protocol and dessert classes are written, but dessert.py cannot find one of the names it uses.",
  "items": [
    {
      "test_key": "order_combine",
      "what_went_wrong": "Loading dessert.py fails with \"name 'Combinable' is not defined\".",
      "hint": "Where does the name Combinable come from? Can you compare it with how Packaging and Payable get into dessert.py?"
    }
  ],
  "next_step": "Check the top of dessert.py."
}
```
