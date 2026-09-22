<!-- p2-review | case=p2_lab2_owner_not_on_self | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_owner_not_on_self

**Lab 2: Bank Account Class** · `cascading_failure` · owner assigned to a local variable instead of self.owner

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -7,5 +7,5 @@
     def __init__(self, owner: str = "", balance: float = 0.0) -> None:
         """Initialize account owner and balance."""
-        self.owner = owner
+        owner = owner
         self.balance = float(balance)
```

## What the grader reported

- `account_init` (Account class initializes owner, balance, and account_number attributes): `E    +  where None = getattr(<account.Account object at 0x10b2002f0>, 'owner', None)`
- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   AttributeError: 'Account' object has no attribute 'owner'`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E   AttributeError: 'Account' object has no attribute 'owner'`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your Account class is missing some attribute assignments during initialization, which is causing errors when trying to access those values later.

**Account class initializes owner, balance, and account_number attributes**: The 'owner' attribute is not being stored on the object during initialization.
- 💡 How do you assign a value to an instance attribute using 'self'?

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: The __str__ method is trying to access 'self.owner', but that attribute does not exist.
- 💡 If the initialization fails to create the attribute, what happens when the string method tries to read it?

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: The demo script fails because it cannot find the 'owner' attribute when printing the account.
- 💡 How does this relate to the missing assignment in your __init__ method?

**Next step:** Review the __init__ method in account.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_init`, `account_str`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('assign using self'). Now compares the owner line with the balance line right below it.

status: todo

```json
{
  "summary": "Your balance handling works, but the owner is never stored on the account, and everything that prints the owner fails.",
  "items": [
    {
      "test_key": "account_init",
      "what_went_wrong": "A new Account has no owner attribute.",
      "hint": "Compare the owner line in __init__ with the balance line right below it. What is different?"
    },
    {
      "test_key": "account_str",
      "what_went_wrong": "__str__ fails with \"'Account' object has no attribute 'owner'\".",
      "hint": "This follows from __init__. Fix that first."
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py fails with the same error when it prints an account.",
      "hint": "This clears once owner is stored."
    }
  ],
  "next_step": "Review the __init__ method in account.py."
}
```
