<!-- p2-review | case=p2_ds3_duplicate_test_name | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds3_duplicate_test_name

**Dessert Shop 3: Test Cases with pytest** · `single_failure` · two tests share one name, so the second replaces the first and the count drops

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/test_dessert.py
+++ student/test_dessert.py
@@ -24,5 +24,5 @@
     assert candy.price_per_pound == 0.0
 
-def test_candy_parameterized():
+def test_candy_default():
     candy = Candy("Gummy Bears", 1.5, 5.99)
     assert candy.name == "Gummy Bears"
@@ -45,5 +45,5 @@
     assert cookie.price_per_dozen == 0.0
 
-def test_cookie_parameterized():
+def test_cookie_default():
     cookie = Cookie("Chocolate Chip", 12, 12.99)
     assert cookie.name == "Chocolate Chip"
```

## What the grader reported

- `student_tests_pass` (Student test suite executes cleanly and passes all assertions): `E   ============================== 13 ...`
- Passing: DS2 class hierarchy and Order class methods intact, test_dessert.py exists and defines at least 15 valid test functions

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your submission contains the correct class hierarchy and logic, but the test suite is missing the required number of test functions.

**Student test suite executes cleanly and passes all assertions**: The test suite only contains 13 passing tests, but the assignment requires at least 15.
- 💡 How many unique test functions are currently defined in your test_dessert.py file?

**Next step:** Review the assignment requirements to see how many additional test cases you need to add to test_dessert.py.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `student_tests_pass`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): next_step told the student to add tests; the tests exist, but two names are reused so pytest only keeps one of each. Hint points to the names.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your classes pass and your tests are written, but pytest is counting fewer tests than you wrote.",
  "items": [
    {
      "test_key": "student_tests_pass",
      "what_went_wrong": "Only 13 tests ran and passed; the assignment needs at least 15.",
      "hint": "How many test functions did you write in test_dessert.py, and how many different names do they have?"
    }
  ],
  "next_step": "Review the test function names in test_dessert.py."
}
```
