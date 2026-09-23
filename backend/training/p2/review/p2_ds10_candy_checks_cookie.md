<!-- p2-review | case=p2_ds10_candy_checks_cookie | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_candy_checks_cookie

**Dessert Shop 10: Combine Like Items** · `cascading_failure` · Candy.can_combine checks isinstance(other, Cookie) (copy-paste)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -67,5 +67,5 @@
 
     def can_combine(self, other: Combinable) -> bool:
-        if isinstance(other, Candy):
+        if isinstance(other, Cookie):
             return self.name == other.name and self.price_per_pound == other.price_per_pound
         return False
```

## What the grader reported

- `candy_combinable` (Candy implements Combinable protocol merging candy_weight for matching items): `E    +    where can_combine = <dessert.Candy object at 0x1090923c0>.can_combine`
- `order_combine` (Order.add() automatically combines like items when matching item is present): `E    +  where 3 = len(<dessert.Order object at 0x109093230>)`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Cookie implements Combinable protocol merging cookie_quantity for matching items, DS9 Order.sort() and relational comparison operators intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the Combinable protocol and the Cookie class logic. However, there are issues with how Candy identifies compatible items and how the Order class handles the combining process.

**Candy implements Combinable protocol merging candy_weight for matching items**: The can_combine method for Candy is currently checking if the other item is a Cookie instead of another Candy.
- 💡 How should the method determine if two Candy items are 'like' items?

**Order.add() automatically combines like items when matching item is present**: The Order.add() method is adding items to the list without successfully merging them into existing entries.
- 💡 When adding an item, how can you check if an item that satisfies can_combine() already exists in the order?

**Next step:** Review the can_combine method in the Candy class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `candy_combinable`, `order_combine`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): what_went_wrong gave the fix (Cookie instead of Candy). Now states the behavior and points at the type check; order_combine follows from it.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your Combinable protocol and the Cookie logic work. One check in Candy keeps matching candies from combining, and the order test follows from it.",
  "items": [
    {
      "test_key": "candy_combinable",
      "what_went_wrong": "Candy.can_combine returns False for two candies with the same name and price.",
      "hint": "Double check your code: read the type check at the top of Candy.can_combine. Which kind of object is it looking for?"
    },
    {
      "test_key": "order_combine",
      "what_went_wrong": "The order keeps 3 items instead of 2 because the candies never combine.",
      "hint": "This follows from the can_combine problem. Fix that first."
    }
  ],
  "next_step": "Review the can_combine method in the Candy class."
}
```
