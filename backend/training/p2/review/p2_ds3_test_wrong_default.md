<!-- p2-review | case=p2_ds3_test_wrong_default | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds3_test_wrong_default

**Dessert Shop 3: Test Cases with pytest** · `single_failure` · student's own test expects Candy() weight 1.0

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/test_dessert.py
+++ student/test_dessert.py
@@ -21,5 +21,5 @@
     candy = Candy()
     assert candy.name == ""
-    assert candy.candy_weight == 0.0
+    assert candy.candy_weight == 1.0
     assert candy.price_per_pound == 0.0
```

## What the grader reported

- `student_tests_pass` (Student test suite executes cleanly and passes all assertions): `E   test_dessert.py::test_sundae_parameterized PASSED        ...`
- Passing: DS2 class hierarchy and Order class methods intact, test_dessert.py exists and defines at least 15 valid test functions

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your test suite is mostly successful, but one specific test case is causing the overall suite to fail.

**Student test suite executes cleanly and passes all assertions**: The test suite failed because the test_candy_default function did not pass.
- 💡 Compare the expected value for candy_weight in your test to the default value defined in your Candy class constructor.

**Next step:** Review the Candy class constructor in dessert.py and the test_candy_default function in test_dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `student_tests_pass`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: accurate and points to the comparison the student should make.

status: todo

```json
{
  "summary": "Your classes and most of your tests are correct, but one of your own tests is failing.",
  "items": [
    {
      "test_key": "student_tests_pass",
      "what_went_wrong": "The test suite failed because test_candy_default did not pass.",
      "hint": "Compare the expected value for candy_weight in your test with the default value in your Candy class constructor. Which one matches the assignment?"
    }
  ],
  "next_step": "Review test_candy_default in test_dessert.py."
}
```
