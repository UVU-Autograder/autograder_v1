<!-- p2-review | case=p2_ds3_test_wrong_sundae | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds3_test_wrong_sundae

**Dessert Shop 3: Test Cases with pytest** · `single_failure` · student's own sundae test expects topping_price 0.9 instead of 0.99

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/test_dessert.py
+++ student/test_dessert.py
@@ -95,5 +95,5 @@
     assert sundae.price_per_scoop == 3.50
     assert sundae.topping_name == "Hot Fudge"
-    assert sundae.topping_price == 0.99
+    assert sundae.topping_price == 0.9
 
 def test_sundae_mutable():
```

## What the grader reported

- `student_tests_pass` (Student test suite executes cleanly and passes all assertions): `E   test_dessert.py::test_sundae_parameterized FAILED        ...`
- Passing: DS2 class hierarchy and Order class methods intact, test_dessert.py exists and defines at least 15 valid test functions

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Most of your test cases are passing, but there is a failure in your parameterized test for the Sundae class.

**Student test suite executes cleanly and passes all assertions**: The test suite failed because one of the assertions in test_sundae_parameterized did not match the expected value.
- 💡 Compare the value you assigned to topping_price in the test setup with the value you are checking in the assertion.

**Next step:** Review the test_sundae_parameterized function in test_dessert.py

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `student_tests_pass`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the comparison the student should make.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Most of your tests pass, but one assertion in your Sundae test does not match.",
  "items": [
    {
      "test_key": "student_tests_pass",
      "what_went_wrong": "The suite failed because one assertion in test_sundae_parameterized did not match.",
      "hint": "Compare the value you passed for topping_price when creating the Sundae with the value you check in the assertion."
    }
  ],
  "next_step": "Review the test_sundae_parameterized function in test_dessert.py."
}
```
