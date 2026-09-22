<!-- p2-review | case=p2_lab2_all_pass_repr | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_all_pass_repr

**Lab 2: Bank Account Class** · `all_pass` · valid alternative: defines __repr__ instead of __str__ (str() falls back to it)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -10,5 +10,5 @@
         self.balance = float(balance)
 
-    def __str__(self) -> str:
+    def __repr__(self) -> str:
         """Return formatted string representation of account."""
         return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
```

## What the grader reported

- All automated checks passed.
- Passing: Account class initializes owner, balance, and account_number attributes, Account __str__() formats output as 'Owner: [owner], Balance: $[balance]', demo.py executes test deposits, withdrawals, and prints account summary to stdout

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Congratulations! Your submission passed all the automated tests and met the requirements.

**Next step:** Consider how you might use a loop to process a list of transactions for an Account object.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Extension now about the student's choice: __repr__ passes only because print() falls back to it.

status: todo

```json
{
  "summary": "Congratulations! Your Account class passes all the automated tests.",
  "items": [],
  "next_step": "Your class defines __repr__, and print() uses it because there is no __str__. Look up the difference between __str__ and __repr__ and decide which one this lab is asking for."
}
```
