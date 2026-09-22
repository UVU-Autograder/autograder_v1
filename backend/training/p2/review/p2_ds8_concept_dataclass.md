<!-- p2-review | case=p2_ds8_concept_dataclass | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds8_concept_dataclass

**Dessert Shop 8: Payment Method** · `concept_violation` · dessertshop.py adds a @dataclass Customer (data classes, Module 11) in a Module 10 project; tests pass

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessertshop.py
+++ student/dessertshop.py
@@ -1,2 +1,10 @@
+from dataclasses import dataclass
+
+
+@dataclass
+class Customer:
+    name: str
+
+
 from dessert import Candy, Cookie, IceCream, Order, Sundae
 from tabulate import tabulate
```

## What the grader reported

- All automated checks passed.
- Passing: PayType Enum (CASH, CARD, PHONE) and Payable protocol defined in payment.py, Order implements get_pay_type() and set_pay_type() with PayType enum validation, Student test_order.py exists with at least 5 test cases validating Order methods, DS7 packaging interface, class structure, and output formatting intact
- Concept warnings (shown to the student in the Warnings panel): concept_warning: [dessertshop.py] Concept 'dataclasses' is not in the allowed list

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! All of your tests passed successfully.

**Next step:** You might consider exploring how to use the 'exceptions' concept to handle invalid user inputs more robustly in your prompt methods.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft ignored the concept warning. Now it does not call the work done and points back to the allowed concepts.

status: todo

```json
{
  "summary": "All the tests pass and your payment logic works.",
  "items": [],
  "next_step": "Your dessertshop.py adds a dataclass, which comes in a later module. Review this module's allowed concepts and write Customer as a regular class for now."
}
```
