<!-- p2-review | case=p2_lab2_demo_bad_import | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab2_demo_bad_import

**Lab 2: Bank Account Class** · `single_failure` · demo.py imports from a module named Account (wrong file name case)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/demo.py
+++ student/demo.py
@@ -1,5 +1,5 @@
 """Demo module for testing Account class - Lab 2 Support File."""
 
-from account import Account
+from Account import Account
```

## What the grader reported

- `demo_output` (demo.py executes test deposits, withdrawals, and prints account summary to stdout): `E    +  where False = hasattr(None, 'Account')`
- Passing: Account class initializes owner, balance, and account_number attributes, Account __str__() formats output as 'Owner: [owner], Balance: $[balance]'

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your Account class is correctly implemented, but the demo script is not producing the expected output during the automated test.

**demo.py executes test deposits, withdrawals, and prints account summary to stdout**: The test expected to see specific account information in the standard output, but the output was empty.
- 💡 How can you ensure that the `main()` function in `demo.py` is actually executed when the test imports the module?

**Next step:** Review the `if __name__ == "__main__":` block in `demo.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `demo_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft misdiagnosed a main() / __name__ problem. demo.py never gets past its import line; the hint asks the student to run it and compare the import with the file name.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your Account class is correct, but demo.py does not run.",
  "items": [
    {
      "test_key": "demo_output",
      "what_went_wrong": "Running demo.py printed nothing, and the test could not reach Account through demo.py.",
      "hint": "Can you run demo.py yourself? Does it get past its first import line? Compare that line with the name of the file your class lives in."
    }
  ],
  "next_step": "Review the import line at the top of demo.py."
}
```
