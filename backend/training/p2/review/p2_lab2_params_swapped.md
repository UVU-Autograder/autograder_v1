<!-- p2-review | case=p2_lab2_params_swapped | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_params_swapped

**Lab 2: Bank Account Class** · `cascading_failure` · __init__ parameters in the wrong order, so Account('Alice', 100.0) calls float('Alice')

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -5,5 +5,5 @@
     """Represents a bank account with owner name and balance."""
 
-    def __init__(self, owner: str = "", balance: float = 0.0) -> None:
+    def __init__(self, balance: float = 0.0, owner: str = "") -> None:
         """Initialize account owner and balance."""
         self.owner = owner
```

## What the grader reported

- `account_init` (Account class initializes owner, balance, and account_number attributes): `E   ValueError: could not convert string to float: 'Alice'`
- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   ValueError: could not convert string to float: 'Alice'`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   ValueError: could not convert string to float: 'Alice'`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your code is currently encountering a ValueError during the initialization of the Account class.

**Account class initializes owner, balance, and account_number attributes**: The code is trying to convert the owner's name string into a float.
- 💡 What order are the arguments being passed into the __init__ method compared to how they are defined in the function signature?

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: This failure follows from the error in the initialization process.
- 💡 If the object cannot be created, can its string representation be accessed?

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: This failure follows from the error in the initialization process.
- 💡 If the object cannot be created, can the demo script proceed?

**Next step:** Review the parameter order in the Account.__init__ method signature.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_init`, `account_str`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate, one root cause, the others follow.

status: accepted

```json
{
  "summary": "Your Account class fails as soon as it is created with an owner and balance.",
  "items": [
    {
      "test_key": "account_init",
      "what_went_wrong": "Account('Alice', 100.0) fails with \"could not convert string to float: 'Alice'\".",
      "hint": "What order are the values passed in, compared with the order the parameters are defined in __init__?"
    },
    {
      "test_key": "account_str",
      "what_went_wrong": "This follows from the error when the account is created.",
      "hint": "If the object cannot be created, its string cannot be checked. Fix __init__ first."
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py fails the same way.",
      "hint": "This clears once __init__ is fixed."
    }
  ],
  "next_step": "Review the parameter order in the Account.__init__ signature."
}
```
