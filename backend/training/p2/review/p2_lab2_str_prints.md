<!-- p2-review | case=p2_lab2_str_prints | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_str_prints

**Lab 2: Bank Account Class** · `cascading_failure` · __str__ prints the text instead of returning it (returns None)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -12,3 +12,3 @@
     def __str__(self) -> str:
         """Return formatted string representation of account."""
-        return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
+        print(f"Owner: {self.owner}, Balance: ${self.balance:.2f}")
```

## What the grader reported

- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   TypeError: __str__ returned non-string (type NoneType)`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   TypeError: __str__ returned non-string (type NoneType)`
- Passing: Account class initializes owner, balance, and account_number attributes

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your account initialization is working correctly, but there is an issue with how the account's string representation is being handled.

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: The __str__ method is returning None instead of the formatted string.
- 💡 What is the difference between printing a value inside a method and returning a value from a method?

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: This failure follows from the issue in the __str__ method.
- 💡 How does the print() function interact with the return value of __str__?

**Next step:** Review the definition of the __str__ method in the Account class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_str`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: the print-versus-return question is exactly the right hint.

status: todo

```json
{
  "summary": "Your account initialization works, but printing an account fails.",
  "items": [
    {
      "test_key": "account_str",
      "what_went_wrong": "str(account) fails with \"__str__ returned non-string (type NoneType)\".",
      "hint": "What is the difference between printing a value inside a method and returning a value from it?"
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py fails the same way when it prints an account.",
      "hint": "This follows from the __str__ problem. Fix that first."
    }
  ],
  "next_step": "Review the __str__ method in the Account class."
}
```
