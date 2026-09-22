<!-- p2-review | case=p2_ds8_valid_types_lowercase | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_valid_types_lowercase

**Dessert Shop 8: Payment Method** · `cascading_failure` · VALID_PAY_TYPES in lowercase, so every valid upper-case type is rejected

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -7,5 +7,5 @@
 from payment import Payable, PayType
 
-VALID_PAY_TYPES = ("CASH", "CARD", "PHONE")
+VALID_PAY_TYPES = ("cash", "card", "phone")
```

## What the grader reported

- `order_payable` (Order implements get_pay_type() and set_pay_type() with PayType enum validation): `E   ValueError: Invalid payment method: CARD`
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, Student test_order.py exists with at least 5 test cases validating Order methods, DS7 packaging interface, class structure, and output formatting intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the Order class is correctly structured, but there is an issue with how payment types are validated.

**Order implements get_pay_type() and set_pay_type() with PayType enum validation**: The set_pay_type method raised a ValueError even though 'CARD' is a valid payment method.
- 💡 Compare the values in your VALID_PAY_TYPES tuple with the expected PayType values defined in payment.py.

**Next step:** Review the PayType definition in payment.py and the VALID_PAY_TYPES constant in dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_payable`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the comparison.

status: todo

```json
{
  "summary": "Your Order class is correctly structured, but it rejects payment types it should accept.",
  "items": [
    {
      "test_key": "order_payable",
      "what_went_wrong": "set_pay_type('CARD') raised a ValueError even though CARD is a valid payment type.",
      "hint": "Compare the values in your VALID_PAY_TYPES tuple with the PayType values defined in payment.py, character by character."
    }
  ],
  "next_step": "Review VALID_PAY_TYPES in dessert.py next to PayType in payment.py."
}
```
