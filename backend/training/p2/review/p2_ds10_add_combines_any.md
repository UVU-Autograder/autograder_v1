<!-- p2-review | case=p2_ds10_add_combines_any | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_add_combines_any

**Dessert Shop 10: Combine Like Items** · `cascading_failure` · Order.add calls combine without checking can_combine first

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -165,5 +165,5 @@
         if isinstance(item, Combinable):
             for existing in self.order:
-                if isinstance(existing, Combinable) and existing.can_combine(item):
+                if isinstance(existing, Combinable):
                     existing.combine(item)
                     return
```

## What the grader reported

- `order_combine` (Order.add() automatically combines like items when matching item is present): `E    +  where 1 = len(<dessert.Order object at 0x00000191E57DA660>)`
- `ds9_regression` (DS9 Order.sort() and relational comparison operators intact): `E     Use -v to get more diff`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Candy implements Combinable protocol merging candy_weight for matching items, Cookie implements Combinable protocol merging cookie_quantity for matching items

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the Combinable protocol and the logic for Candy and Cookie items. However, the Order class is not correctly merging items during the addition process.

**Order.add() automatically combines like items when matching item is present**: The Order object contains two separate instances of the same item instead of merging them into one.
- 💡 When adding an item to the Order, how does your code check if an identical item already exists in the list?

**Next step:** Review the Order.add() method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_combine`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft had it backwards (said items were NOT merged); the test found 1 item where 2 should stay separate. Order.add is cut off from the prompt, so the feedback reasons from the assertion.

> Updated after 4159d52 (Claude): The stricter tests also fail ds9_regression: the sort test adds two different candies, and Order.add merges them. Added as a follow-on item.

status: accepted

```json
{
  "summary": "Your Combinable protocol and the Candy and Cookie combine methods are in place. Order.add is merging items that should stay separate, and a Dessert Shop 9 test trips over the same thing.",
  "items": [
    {
      "test_key": "order_combine",
      "what_went_wrong": "The test expected 2 items in the order but found 1, so two items that should not combine were merged into one.",
      "hint": "When Order.add finds an item already in the order, what does it check before merging the two? Can you trace it by hand with two different candies?"
    },
    {
      "test_key": "ds9_regression",
      "what_went_wrong": "The sorting test adds two different candies, and they get merged before sort() runs, so the order is wrong.",
      "hint": "This follows from the Order.add problem. Fix that first."
    }
  ],
  "next_step": "Review the Order.add method in dessert.py."
}
```
