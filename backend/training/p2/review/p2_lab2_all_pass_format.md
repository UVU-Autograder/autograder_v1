<!-- p2-review | case=p2_lab2_all_pass_format | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_all_pass_format

**Lab 2: Bank Account Class** · `all_pass` · valid alternative: str.format instead of an f-string

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -12,3 +12,3 @@
     def __str__(self) -> str:
         """Return formatted string representation of account."""
-        return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
+        return "Owner: {}, Balance: ${:.2f}".format(self.owner, self.balance)
```

## What the grader reported

- All automated checks passed.
- Passing: Account class initializes owner, balance, and account_number attributes, Account __str__() formats output as 'Owner: [owner], Balance: $[balance]', demo.py executes test deposits, withdrawals, and prints account summary to stdout

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Great job! Your implementation of the Account class passed all the automated tests.

**Next step:** Consider how you might add a method to handle interest calculations using the allowed concepts.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Generic extension replaced with one about the student's own choice (str.format).

status: todo

```json
{
  "summary": "Great job! Your Account class passes all the automated tests.",
  "items": [],
  "next_step": "You used str.format instead of an f-string, and both work. Can you write the same line as an f-string and decide which one reads more clearly?"
}
```
