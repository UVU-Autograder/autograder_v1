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
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, Student test_order.py exists with at least 5 test cases validating Order methods, DS7 packaging interface, class structure, and output formatting intact

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

status: todo

```json
{
  "summary": "Your protocols and Order class work, and set_pay_type does reject invalid values. It reports them with a different kind of error than the test expects.",
  "items": [
    {
      "test_key": "order_payable",
      "what_went_wrong": "set_pay_type('INVALID') raised a TypeError, and the test did not accept that exception.",
      "hint": "The value is a string, the right type, but not one of the allowed options. Which built-in exception is meant for that situation?"
    }
  ],
  "next_step": "Review the raise line in set_pay_type in dessert.py."
}
```
