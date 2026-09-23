<!-- p2-review | case=p2_ds2_concept_file_io | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_concept_file_io

**Dessert Shop 2: Using Classes in main** · `concept_violation` · main also writes the receipt to a file (file I/O, Module 11); tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -15,4 +15,6 @@
 
     print("Total number of items in order:", len(order))
+    with open("receipt.txt", "w") as receipt:
+        receipt.write(str(len(order)))
```

## What the grader reported

- All automated checks passed.
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae), Order class defines order list, add() method, and len() support, dessertshop.py main() constructs Order items and prints formatted receipt
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [dessertshop.py] Concept 'file-io' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your code passed all the automated tests for the Dessert Shop assignment.

**Next step:** You might consider exploring how to use properties to create read-only attributes for your dessert items.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft ignored the concept warning and suggested an unrelated extension. Now it does not call the work done, and points back to the allowed concepts.

status: accepted

```json
{
  "summary": "All the tests pass and your Order class works.",
  "items": [],
  "next_step": "Your main also writes a receipt file, which uses file I/O from a later module. Review this module's allowed concepts and keep main to printing for now."
}
```
