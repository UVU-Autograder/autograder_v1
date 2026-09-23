<!-- p2-review | case=p2_lab2_class_lowercase | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_class_lowercase

**Lab 2: Bank Account Class** · `cascading_failure` · class named account instead of Account

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -2,5 +2,5 @@
 
 
-class Account:
+class account:
     """Represents a bank account with owner name and balance."""
```

## What the grader reported

- `account_init` (Account class initializes owner, balance, and account_number attributes): `E   AttributeError: module 'account' has no attribute 'Account'. Did you mean: 'account'?`
- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   AttributeError: module 'account' has no attribute 'Account'. Did you mean: 'account'?`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   ImportError: cannot import name 'Account' from 'account' (/private/var/folders/wh/1wdfmd9n0kn0xwvpnwp_t2yc0000gq/T/ag_grade_z9qad_cr/execution/account.py). Did you mean: 'account'?`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

The autograder is unable to find the Account class because of a naming mismatch in your class definition.

**Account class initializes owner, balance, and account_number attributes**: The test script cannot find a class named 'Account' within your module.
- 💡 How does the capitalization of your class name in account.py compare to how it is being imported in the test file?

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: The test script cannot find a class named 'Account' within your module.
- 💡 This follows from the naming issue in the initialization test.

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: The demo script failed to import the required class.
- 💡 This follows from the naming issue in the initialization test.

**Next step:** Review the class definition in account.py to ensure it matches the expected name.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_init`, `account_str`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: the hint now points at the error message instead of the test file, which the student cannot see.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your Account logic is written, but nothing can find the class by the name the assignment uses.",
  "items": [
    {
      "test_key": "account_init",
      "what_went_wrong": "The test cannot find a class named Account in account.py.",
      "hint": "The error ends with \"Did you mean: 'account'?\". How does the capitalization of your class name compare with the name the assignment uses?"
    },
    {
      "test_key": "account_str",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This follows from the class name. Fix that first."
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py cannot import Account for the same reason.",
      "hint": "This clears once the class name matches."
    }
  ],
  "next_step": "Review the class line in account.py."
}
```
