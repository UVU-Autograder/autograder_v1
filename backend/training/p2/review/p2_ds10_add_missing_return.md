<!-- p2-review | case=p2_ds10_add_missing_return | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_add_missing_return

**Dessert Shop 10: Combine Like Items** · `single_failure` · Order.add combines but then also appends (missing return)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -167,5 +167,4 @@
                 if isinstance(existing, Combinable) and existing.can_combine(item):
                     existing.combine(item)
-                    return
         self.order.append(item)
```

## What the grader reported

- `order_combine` (Order.add() automatically combines like items when matching item is present): `E    +  where 3 = len(<dessert.Order object at 0x106f2aa50>)`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Candy implements Combinable protocol merging candy_weight for matching items, Cookie implements Combinable protocol merging cookie_quantity for matching items, DS9 Order.sort() and relational comparison operators intact
- **The changed lines are cut off by the prompt's code budget: the model sees the failure, not the code.** Good feedback here reasons from the assertion alone.

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the Combinable protocol and the logic for Candy and Cookie classes. However, the Order class is not yet correctly merging items during the addition process.

**Order.add() automatically combines like items when matching item is present**: The Order object contains three items instead of two, indicating that a new item was added to the list instead of being merged with an existing one.
- 💡 When adding an item to the Order, how does your code check if an item that can be combined already exists in the list?

**Next step:** Review the Order.add() method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_combine`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft said the item was added instead of merged; it was merged and then also added (3 items, not 2). Hint now asks what runs after the merge.

status: todo

```json
{
  "summary": "Your Combinable protocol and the Candy and Cookie classes are working. Order.add is doing the merge, but not only the merge.",
  "items": [
    {
      "test_key": "order_combine",
      "what_went_wrong": "The order ended up with 3 items where the test expected 2, so an item that was merged into an existing one was also added to the list.",
      "hint": "Trace Order.add for an item that matches one already in the order. After the merge happens, which lines still run?"
    }
  ],
  "next_step": "Review the Order.add method in dessert.py."
}
```
