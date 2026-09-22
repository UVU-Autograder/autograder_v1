<!-- p2-review | case=p2_ds10_cookie_adds_price | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds10_cookie_adds_price

**Dessert Shop 10: Combine Like Items** · `single_failure` · Cookie.combine adds to price_per_dozen instead of cookie_quantity

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -101,5 +101,5 @@
     def combine(self, other: Combinable) -> "Cookie":
         if self.can_combine(other) and isinstance(other, Cookie):
-            self.cookie_quantity += other.cookie_quantity
+            self.price_per_dozen += other.price_per_dozen
         return self
```

## What the grader reported

- `cookie_combinable` (Cookie implements Combinable protocol merging cookie_quantity for matching items): `E    +  where 12 = <dessert.Cookie object at 0x107ccaba0>.cookie_quantity`
- Passing: Combinable protocol defined in combine.py with can_combine() and combine() methods, Candy implements Combinable protocol merging candy_weight for matching items, Order.add() automatically combines like items when matching item is present, DS9 Order.sort() and relational comparison operators intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the Combinable protocol and handles Candy and Order logic correctly. However, there is an issue with how Cookie quantities are merged.

**Cookie implements Combinable protocol merging cookie_quantity for matching items**: The cookie_quantity is not being updated correctly when two cookies are combined.
- 💡 In your Cookie.combine method, which attribute are you currently updating instead of cookie_quantity?

**Next step:** Review the Cookie.combine method in dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `cookie_combinable`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: what_went_wrong now uses the numbers from the assertion. The hint was already good.

status: todo

```json
{
  "summary": "Your Combinable protocol, Candy merging and Order logic work. Cookies combine, but the quantity does not change.",
  "items": [
    {
      "test_key": "cookie_combinable",
      "what_went_wrong": "After combining, the first cookie still has 12 cookies; the test expects 18.",
      "hint": "In your Cookie.combine method, which attribute are you currently updating instead of cookie_quantity?"
    }
  ],
  "next_step": "Review the Cookie.combine method in dessert.py."
}
```
