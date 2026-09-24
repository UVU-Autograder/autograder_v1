<!-- p2-review | case=p2_ds8_getter_wrong_attr | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_getter_wrong_attr

**Dessert Shop 8: Payment Method** · `cascading_failure` · get_pay_type returns self.pay_type, which does not exist

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -120,5 +120,5 @@
 
     def get_pay_type(self) -> PayType:
-        return self._pay_type
+        return self.pay_type
 
     def set_pay_type(self, payment_method: PayType) -> None:
```

## What the grader reported

- `order_payable` (Order implements get_pay_type() and set_pay_type() with PayType enum validation): `E   AttributeError: 'Order' object has no attribute 'pay_type'`
- `student_order_tests` (Student test_order.py exists with at least 5 test cases validating Order methods): `E   dessert.p...`
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, DS7 packaging interface, class structure, and output formatting intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the required protocols and packaging structures, but there is an issue with how the payment type is being accessed.

**Order implements get_pay_type() and set_pay_type() with PayType enum validation**: The `get_pay_type` method is trying to return an attribute that does not exist on the `Order` object.
- 💡 Look at the variable name you defined in the `__init__` method of the `Order` class and compare it to the attribute name used in `get_pay_type`.

**Next step:** Review the `Order` class in `dessert.py` to ensure the attribute names are consistent.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_payable`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the comparison.

> Updated after 4159d52 (Claude): The stricter grading now runs the student's own test_order.py, which fails on the same bug. Added as a follow-on item.

status: todo

```json
{
  "summary": "Your submission implements the required protocols, but get_pay_type reaches for an attribute that does not exist. Your own tests caught it too.",
  "items": [
    {
      "test_key": "order_payable",
      "what_went_wrong": "get_pay_type() fails with \"'Order' object has no attribute 'pay_type'\".",
      "hint": "Look at the attribute name you set in the Order __init__ and compare it with the one get_pay_type returns."
    },
    {
      "test_key": "student_order_tests",
      "what_went_wrong": "Your pay-type tests in test_order.py fail for the same reason.",
      "hint": "This follows from get_pay_type. Your tests are doing their job: fix the method, not the tests."
    }
  ],
  "next_step": "Review get_pay_type in the Order class in dessert.py."
}
```
