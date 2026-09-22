<!-- p2-review | case=p2_ds8_regression_packaging | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_regression_packaging

**Dessert Shop 8: Payment Method** · `single_failure` · Candy packaging changed to Box (DS7 regression)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -30,5 +30,5 @@
 
     def __init__(self, name: str = "", candy_weight: float = 0.0, price_per_pound: float = 0.0) -> None:
-        super().__init__(name, "Bag")
+        super().__init__(name, "Box")
         self.candy_weight = candy_weight
         self.price_per_pound = price_per_pound
```

## What the grader reported

- `ds7_regression` (DS7 packaging interface, class structure, and output formatting intact): `E     + Box`
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, Order implements get_pay_type() and set_pay_type() with PayType enum validation, Student test_order.py exists with at least 5 test cases validating Order methods

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the required payment protocols and order methods, but there is a regression in the packaging logic.

**DS7 packaging interface, class structure, and output formatting intact**: The packaging for a specific dessert item is being set to 'Box' instead of the expected 'Bag'.
- 💡 Check the `__init__` method of the dessert classes to see which string is being passed to the superclass constructor.

**Next step:** Review the `Candy` and `Cookie` class definitions in `dessert.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `ds7_regression`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): next_step sent the student to Cookie too; only Candy changed. Now names the Dessert Shop 7 behavior that broke.

status: todo

```json
{
  "summary": "Your payment protocol and Order methods work. One Dessert Shop 7 behavior has broken.",
  "items": [
    {
      "test_key": "ds7_regression",
      "what_went_wrong": "A new Candy's packaging is 'Box'; the Dessert Shop 7 test expects 'Bag'.",
      "hint": "Check what Candy's __init__ passes to the superclass for packaging. Does it match the packaging the assignment lists for candy?"
    }
  ],
  "next_step": "Review the Candy class __init__ in dessert.py."
}
```
