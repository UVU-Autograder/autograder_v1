<!-- p2-review | case=p2_ds8_default_lowercase | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_default_lowercase

**Dessert Shop 8: Payment Method** · `single_failure` · default pay type is 'cash' in lowercase

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -111,5 +111,5 @@
     def __init__(self) -> None:
         self.order: list[DessertItem] = []
-        self._pay_type: PayType = "CASH"
+        self._pay_type: PayType = "cash"
 
     def add(self, item: DessertItem) -> None:
```

## What the grader reported

- `order_payable` (Order implements get_pay_type() and set_pay_type() with PayType enum validation): `E     + cash`
- `student_order_tests` (Student test_order.py exists with at least 5 test cases validating Order methods): `E   Std...`
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, DS7 packaging interface, class structure, and output formatting intact

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission successfully implements the required protocols and class structures, but there is a mismatch in the payment type value.

**Order implements get_pay_type() and set_pay_type() with PayType enum validation**: The `get_pay_type()` method returned the lowercase string 'cash', but the test expected the uppercase string 'CASH'.
- 💡 Check the initial value assigned to `self._pay_type` in the `Order` class constructor.

**Next step:** Review the `Order.__init__` method in `dessert.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_payable`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to where to look.

> Updated after 4159d52 (Claude): The student's own test_order.py now fails too, on the same bug. Added as a follow-on item.

status: accepted

```json
{
  "summary": "Your submission implements the required protocols and class structure, but the default payment type does not match, and your own default test catches it.",
  "items": [
    {
      "test_key": "order_payable",
      "what_went_wrong": "A new Order's get_pay_type() returned 'cash', but the test expects 'CASH'.",
      "hint": "Check the initial value assigned to self._pay_type in the Order constructor, and compare it with the values PayType allows."
    },
    {
      "test_key": "student_order_tests",
      "what_went_wrong": "Your own default-pay-type test fails for the same reason.",
      "hint": "This follows from the default in __init__. Fix that, not the test."
    }
  ],
  "next_step": "Review the Order.__init__ method in dessert.py."
}
```
