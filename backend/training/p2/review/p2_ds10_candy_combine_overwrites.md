<!-- p2-review | case=p2_ds10_candy_combine_overwrites | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_candy_combine_overwrites

**Dessert Shop 10: Combine Like Items** · `single_failure` · Candy.combine assigns the other weight instead of adding it

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -73,5 +73,5 @@
     def combine(self, other: Combinable) -> "Candy":
         if self.can_combine(other) and isinstance(other, Candy):
-            self.candy_weight += other.candy_weight
+            self.candy_weight = other.candy_weight
         return self
```

## What the grader reported

- `candy_combinable` (Candy implements Combinable protocol merging candy_weight for matching items): `E    +  where 2.0 = <dessert.Candy object at 0x0000019DF46A9550>.candy_weight`
- `order_combine` (Order.add() automatically combines like items when matching item is present): `E    +  where 2.0 = <dessert.Candy object at 0x0000019DF46AACF0>.candy_weight`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Cookie implements Combinable protocol merging cookie_quantity for matching items, DS9 Order.sort() and relational comparison operators intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the Combinable protocol and the logic for Cookies, but there is an issue with how Candy items are being merged.

**Candy implements Combinable protocol merging candy_weight for matching items**: The candy weight is being overwritten by the second item's weight instead of being added to the first item's weight.
- 💡 In your Candy.combine method, what mathematical operation should be performed on self.candy_weight?

**Order.add() automatically combines like items when matching item is present**: This failure follows from the incorrect weight calculation in the Candy class.
- 💡 Review how the weight is updated during a combination.

**Next step:** Examine the Candy.combine method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `candy_combinable`, `order_combine`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint asked 'what mathematical operation', which is an either/or in disguise. Now describes what happens to the first candy's weight and points at the line.

status: accepted

```json
{
  "summary": "Your Combinable protocol and Cookie merging work. Candy items combine, but the weight comes out wrong.",
  "items": [
    {
      "test_key": "candy_combinable",
      "what_went_wrong": "After combining, the first candy has a weight of 2.0, which is only the second candy's weight. The test expects 3.0.",
      "hint": "Look at the line in Candy.combine that updates self.candy_weight. What happens to the weight the first candy already had?"
    },
    {
      "test_key": "order_combine",
      "what_went_wrong": "The combined candy in the order has the same wrong weight.",
      "hint": "This follows from the Candy.combine problem. Fix that first."
    }
  ],
  "next_step": "Review the Candy.combine method in dessert.py."
}
```
