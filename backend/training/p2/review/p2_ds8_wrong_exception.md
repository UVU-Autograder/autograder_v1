<!-- p2-review | case=p2_ds8_wrong_exception | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_wrong_exception

**Dessert Shop 8: Payment Method** · `single_failure` · invalid pay type raises TypeError instead of ValueError

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -124,5 +124,5 @@
     def set_pay_type(self, payment_method: PayType) -> None:
         if payment_method not in VALID_PAY_TYPES:
-            raise ValueError(f"Invalid payment method: {payment_method}")
+            raise TypeError(f"Invalid payment method: {payment_method}")
         self._pay_type = payment_method
```

## What the grader reported

- `order_payable` (Order implements get_pay_type() and set_pay_type() with PayType enum validation): `E   TypeError: Invalid payment method: INVALID`
- `student_order_tests` (Student test_order.py exists with at least 5 test cases validating Order methods): `E           if paym...`
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, DS7 packaging interface, class structure, and output formatting intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the required Enums, Protocols, and class structures. However, there is an issue with how payment types are validated.

**Order implements get_pay_type() and set_pay_type() with PayType enum validation**: The `set_pay_type` method raises a `TypeError` when it receives an invalid payment method, but the test expects it to handle the validation differently.
- 💡 How should the method behave if the input is not one of the valid `PayType` options? Check the requirements regarding validation.

**Next step:** Review the `set_pay_type` method in `dessert.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_payable`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft was vague ('handle it differently'). Now states what happened and asks which kind of error fits a wrong value.

> Updated after 4159d52 (Claude): The student's own test_order.py now fails too (it expects the same exception). Added as a follow-on item.

> v8 revision (Claude): removed the test input and the exception name; next step no longer points at the raise line; trimmed

status: accepted

```json
{
  "summary": "Your protocols work and set_pay_type rejects bad values, but with a different exception than the tests expect.",
  "items": [
    {
      "test_key": "order_payable",
      "what_went_wrong": "The invalid pay type check raises the wrong kind of exception.",
      "hint": "Which exception does the test expect for an invalid pay type, and which one does set_pay_type raise?"
    },
    {
      "test_key": "student_order_tests",
      "what_went_wrong": "Your own invalid pay type test fails for the same reason.",
      "hint": "This follows from set_pay_type; fix the method, not your test."
    }
  ],
  "next_step": "Review Order.set_pay_type in dessert.py."
}
```
