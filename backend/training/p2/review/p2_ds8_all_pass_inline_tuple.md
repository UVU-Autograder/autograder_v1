<!-- p2-review | case=p2_ds8_all_pass_inline_tuple | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_all_pass_inline_tuple

**Dessert Shop 8: Payment Method** · `all_pass` · valid alternative: allowed pay types written inline in set_pay_type

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -123,5 +123,5 @@
 
     def set_pay_type(self, payment_method: PayType) -> None:
-        if payment_method not in VALID_PAY_TYPES:
+        if payment_method not in ("CASH", "CARD", "PHONE"):
             raise ValueError(f"Invalid payment method: {payment_method}")
         self._pay_type = payment_method
```

## What the grader reported

- All automated checks passed.
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, Order implements get_pay_type() and set_pay_type() with PayType enum validation, Student test_order.py exists with at least 5 test cases validating Order methods, DS7 packaging interface, class structure, and output formatting intact
- **The changed lines are cut off by the prompt's code budget: the model sees the failure, not the code.** Good feedback here reasons from the assertion alone.

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission passed all the automated tests and follows the required concepts.

**Next step:** Consider exploring how you might use the 'exceptions' concept to handle invalid user inputs more robustly in your prompt methods.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Replaced a generic extension. Order is cut off from the prompt, so the next step is general but points at maintainability.

status: todo

```json
{
  "summary": "Congratulations! Every test passes.",
  "items": [],
  "next_step": "Try adding a fourth payment type, such as GIFT_CARD, and count how many places in your code need to change. Could that number be one?"
}
```
