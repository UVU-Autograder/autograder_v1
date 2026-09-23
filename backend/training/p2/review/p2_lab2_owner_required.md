<!-- p2-review | case=p2_lab2_owner_required | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_owner_required

**Lab 2: Bank Account Class** · `single_failure` · owner has no default, so Account() fails

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -5,5 +5,5 @@
     """Represents a bank account with owner name and balance."""
 
-    def __init__(self, owner: str = "", balance: float = 0.0) -> None:
+    def __init__(self, owner: str, balance: float = 0.0) -> None:
         """Initialize account owner and balance."""
         self.owner = owner
```

## What the grader reported

- `account_init` (Account class initializes owner, balance, and account_number attributes): `E   TypeError: Account.__init__() missing 1 required positional argument: 'owner'`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   TypeError: Account.__init__() missing 1 required positional argument: 'owner'`
- Passing: Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your `__str__` method is working perfectly! However, there is an issue with how the `Account` class is being initialized.

**Account class initializes owner, balance, and account_number attributes**: The `Account` class is being instantiated without providing the required `owner` argument.
- 💡 How can you modify the `__init__` method to allow the `owner` parameter to be optional?

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: The `main` function fails because it tries to create a `default_account` without an owner.
- 💡 If the `account_init` issue is resolved, will this error persist?

**Next step:** Review the `__init__` method signature in `account.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_init`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('make owner optional'). Now compares owner with balance, which already has what owner is missing.

status: accepted

```json
{
  "summary": "Your __str__ method works. Creating an account with no arguments fails.",
  "items": [
    {
      "test_key": "account_init",
      "what_went_wrong": "The test creates Account() with no arguments, and __init__ says owner is required.",
      "hint": "Can you compare how owner and balance are declared in __init__? Why does balance work without a value?"
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py fails the same way when it creates default_account.",
      "hint": "This follows from the __init__ problem. Fix that first."
    }
  ],
  "next_step": "Review the __init__ signature in account.py."
}
```
