<!-- p2-review | case=p2_ds10_not_runtime_checkable | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_not_runtime_checkable

**Dessert Shop 10: Combine Like Items** · `cascading_failure` · @runtime_checkable removed, so isinstance(item, Combinable) raises TypeError

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/combine.py
+++ student/combine.py
@@ -4,5 +4,4 @@
 
 
-@runtime_checkable
 class Combinable(Protocol):
     """Protocol for items that support merging/combining like items."""
```

## What the grader reported

- `order_combine` (Order.add() automatically combines like items when matching item is present): `E   TypeError: Instance and class checks can only be used with @runtime_checkable protocols`
- `ds9_regression` (DS9 Order.sort() and relational comparison operators intact): `E   TypeError: Instance and class checks can only be used with @runtime_checkable protocols`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Candy implements Combinable protocol merging candy_weight for matching items, Cookie implements Combinable protocol merging cookie_quantity for matching items

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the Combinable protocol and its usage in the Order class is mostly correct, but there is a specific issue with how you are checking for protocol compliance at runtime.

**Order.add() automatically combines like items when matching item is present**: The code is attempting to use isinstance() to check if an object follows the Combinable protocol, but the protocol is not configured to allow runtime checks.
- 💡 How can you modify the definition of the Combinable protocol in combine.py to allow it to be used with isinstance()?

**Next step:** Review the documentation or the definition of the @runtime_checkable decorator in combine.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_combine`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint and next step named the decorator (the fix). The error message itself says what is required, so the hint sends the student to read it.

> Updated after 4159d52 (Claude): The stricter tests also fail ds9_regression with the same TypeError. Added as a follow-on item.

status: todo

```json
{
  "summary": "Your Combinable protocol and your combine methods are written. The problem is how the protocol is declared, not how you use it.",
  "items": [
    {
      "test_key": "order_combine",
      "what_went_wrong": "Order.add uses isinstance() with Combinable, and Python refuses because the protocol is not set up for runtime checks.",
      "hint": "Read the last line of the error closely, then look at how Combinable is declared in combine.py. What does the error say the protocol needs?"
    },
    {
      "test_key": "ds9_regression",
      "what_went_wrong": "The Dessert Shop 9 sorting test adds items to an Order, so it hits the same TypeError.",
      "hint": "This follows from the Combinable declaration. Fix that first."
    }
  ],
  "next_step": "Review the Combinable definition in combine.py."
}
```
