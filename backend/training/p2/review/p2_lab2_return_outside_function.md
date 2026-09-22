<!-- p2-review | case=p2_lab2_return_outside_function | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_return_outside_function

**Lab 2: Bank Account Class** · `import_error` · return line dedented out of __str__ (SyntaxError: 'return' outside function)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -12,3 +12,3 @@
     def __str__(self) -> str:
         """Return formatted string representation of account."""
-        return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
+    return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
```

## What the grader reported

- `account_init` (Account class initializes owner, balance, and account_number attributes): `E   SyntaxError: 'return' outside function`
- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   SyntaxError: 'return' outside function`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   SyntaxError: 'return' outside function`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your code is currently encountering a syntax error that prevents the program from running.

**Account class initializes owner, balance, and account_number attributes**: A SyntaxError occurred because a return statement is placed outside of a function body.
- 💡 How is the indentation of the return statement in your __str__ method structured?

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: This failure follows from the syntax error in the Account class.
- 💡 Check the indentation of the return statement in your __str__ method.

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: This failure follows from the syntax error in the Account class.
- 💡 Check the indentation of the return statement in your __str__ method.

**Next step:** Review the indentation of the return statement inside the Account class's __str__ method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_init`, `account_str`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: items 2 and 3 now say they follow from the syntax error instead of repeating the hint.

status: todo

```json
{
  "summary": "Your code has a syntax error, so account.py cannot run yet.",
  "items": [
    {
      "test_key": "account_init",
      "what_went_wrong": "Python reports a SyntaxError on line 14: a return statement is outside a function.",
      "hint": "How is the return line in your __str__ method indented compared with the lines around it?"
    },
    {
      "test_key": "account_str",
      "what_went_wrong": "This follows from the syntax error.",
      "hint": "Fix the syntax error first."
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py cannot import account.py because of the same syntax error.",
      "hint": "This clears once account.py loads."
    }
  ],
  "next_step": "Review the indentation of the __str__ method in account.py."
}
```
