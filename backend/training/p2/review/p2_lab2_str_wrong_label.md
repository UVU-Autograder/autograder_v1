<!-- p2-review | case=p2_lab2_str_wrong_label | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_str_wrong_label

**Lab 2: Bank Account Class** · `single_failure` · __str__ says Name: instead of Owner:

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -12,3 +12,3 @@
     def __str__(self) -> str:
         """Return formatted string representation of account."""
-        return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
+        return f"Name: {self.owner}, Balance: ${self.balance:.2f}"
```

## What the grader reported

- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   assert 'Owner: Alice, Balance: $100.00' in 'Name: Alice, Balance: $100.00'`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   assert ('Owner:' in 'Name: Alice, Balance: $100.00\nName: , Balance: $0.00\n')`
- Passing: Account class initializes owner, balance, and account_number attributes

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your code successfully initializes the account attributes and runs the demo, but there is a formatting issue in the string representation.

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: The output string uses 'Name:' instead of 'Owner:' as the prefix for the owner's name.
- 💡 How can you modify the `__str__` method to match the specific label required by the assignment?

**Next step:** Review the `__str__` method in the `Account` class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_str`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint asked how to 'modify __str__ to match the label' (the fix). Now asks the student to compare word by word.

> Updated after 4159d52 (Claude): The stricter tests now check the full string, and demo_output fails too because demo.py prints 'Name:'. Added as a follow-on item.

status: accepted

```json
{
  "summary": "Your Account initialization works, but the text __str__ produces does not match the required format, so the demo output is off too.",
  "items": [
    {
      "test_key": "account_str",
      "what_went_wrong": "The test expects 'Owner: Alice, Balance: $100.00' but got 'Name: Alice, Balance: $100.00'.",
      "hint": "Can you compare your output with the expected text word by word?"
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py prints the same 'Name:' text, so it is missing the expected 'Owner:' lines.",
      "hint": "This follows from __str__. Fix that first."
    }
  ],
  "next_step": "Review the __str__ method in the Account class."
}
```
