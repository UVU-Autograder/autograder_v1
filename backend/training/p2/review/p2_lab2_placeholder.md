<!-- p2-review | case=p2_lab2_placeholder | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_placeholder

**Lab 2: Bank Account Class** · `empty_submission` · both files are still TODO placeholders

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/account.py
+++ student/account.py
@@ -1,14 +1,2 @@
-"""Bank Account Class - Lab 2 Model Solution."""
-
-
-class Account:
-    """Represents a bank account with owner name and balance."""
-
-    def __init__(self, owner: str = "", balance: float = 0.0) -> None:
-        """Initialize account owner and balance."""
-        self.owner = owner
-        self.balance = float(balance)
-
-    def __str__(self) -> str:
-        """Return formatted string representation of account."""
-        return f"Owner: {self.owner}, Balance: ${self.balance:.2f}"
+"""Lab 2: Bank Account."""
+# TODO: write the Account class
--- model/demo.py
+++ student/demo.py
@@ -1,16 +1 @@
-"""Demo module for testing Account class - Lab 2 Support File."""
-
-from account import Account
-
-
-def main() -> None:
-    """Manual testing entrypoint."""
-    custom_account = Account("Alice", 100.0)
-    default_account = Account()
-
-    print(custom_account)
-    print(default_account)
-
-
-if __name__ == "__main__":
-    main()
+# TODO: demo goes here
```

## What the grader reported

- `account_init` (Account class initializes owner, balance, and account_number attributes): `E   AttributeError: module 'account' has no attribute 'Account'`
- `account_str` (Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'): `E   AttributeError: module 'account' has no attribute 'Account'`
- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E    +  where False = hasattr(<module 'demo' from '/private/var/folders/wh/1wdfmd9n0kn0xwvpnwp_t2yc0000gq/T/ag_grade_pgc5ovr3/execution/demo.py'>, 'Account')`
- The prompt carries SUBMISSION_NOTE: the code is empty or a placeholder.

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

The file is still a placeholder, and the autograder cannot find the required class definition.

**Account class initializes owner, balance, and account_number attributes**: The test script cannot find a class named 'Account' inside your account.py file.
- 💡 How can you define a class in Python so that it is accessible to other modules?

**Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'**: This failure follows from the missing class definition.
- 💡 If the class is defined correctly, will this error persist?

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: The demo script is not producing the expected output because the Account class is missing.
- 💡 What needs to be implemented in account.py and demo.py to produce the required output?

**Next step:** Start from the assignment instructions to define the Account class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `account_init`, `account_str`, `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Tightened for a placeholder: says so plainly, one real item, demo follows from it, and next step starts from the instructions.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Both account.py and demo.py are still placeholders, so there is no Account class to test yet.",
  "items": [
    {
      "test_key": "account_init",
      "what_went_wrong": "The tests could not find an Account class in account.py.",
      "hint": "Which class, and which two attributes, does the assignment ask account.py to define?"
    },
    {
      "test_key": "demo_output",
      "what_went_wrong": "demo.py printed nothing.",
      "hint": "This follows from the missing class: demo.py needs an Account to print."
    }
  ],
  "next_step": "Start from the assignment instructions: write the Account class first, then a demo that prints two accounts."
}
```
