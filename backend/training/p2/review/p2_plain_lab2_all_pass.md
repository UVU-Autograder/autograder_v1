<!-- p2-review | case=p2_plain_lab2_all_pass | drafted_by=claude-pre-edit | prompt=v5 -->
# p2_plain_lab2_all_pass

**Lab 2: Bank Account Class** · `all_pass` · unchanged model solution: nothing unusual to point out

## The bug (ground truth -- the model never sees this diff)

```diff
(no change: model solution as-is)
```

## What the grader reported

- All automated checks passed.
- Passing: Account class initializes owner, balance, and account_number attributes, Account __str__() formats output as 'Owner: [owner], Balance: $[balance]', demo.py executes test deposits, withdrawals, and prints account summary to stdout

## Draft by `claude-pre-edit` (written directly, no model draft), as the student would see it

Great job! Your Account class passes all the automated tests.

**Next step:** Try adding a deposit method that updates the balance, then print an account before and after a deposit in demo.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Plain all-pass case, added because the first adapter invented problems on clean solutions. The next step is an extension that fits the assignment and claims nothing about the student's code.

status: accepted

```json
{
  "summary": "Great job! Your Account class passes all the automated tests.",
  "items": [],
  "next_step": "Try adding a deposit method that updates the balance, then print an account before and after a deposit in demo.py."
}
```
