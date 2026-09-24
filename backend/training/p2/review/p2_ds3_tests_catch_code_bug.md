<!-- p2-review | case=p2_ds3_tests_catch_code_bug | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds3_tests_catch_code_bug

**Dessert Shop 3: Test Cases with pytest** · `cascading_failure` · Cookie default quantity is 1; the student's own test catches it, as does the DS2 regression

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -12,5 +12,5 @@
 
 class Cookie(DessertItem):
-    def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0):
+    def __init__(self, name: str = "", cookie_quantity: int = 1, price_per_dozen: float = 0.0):
         super().__init__(name)
         self.cookie_quantity = cookie_quantity
```

## What the grader reported

- `student_tests_pass` (Student test suite executes cleanly and passes all assertions): `E   t...`
- Passing: DS2 class hierarchy and Order class methods intact, test_dessert.py exists and defines at least 15 valid test functions

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Most of your test suite passed successfully, but there is a specific failure in the cookie tests.

**Student test suite executes cleanly and passes all assertions**: The test suite failed because one of the individual tests in test_dessert.py did not pass.
- 💡 Which specific test function in your suite is reporting a failure?

**Next step:** Review the `test_cookie_default` function in `test_dessert.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `student_tests_pass`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft sent the student to edit the test; here the test is right and Cookie's default is wrong. Feedback credits the test and asks which side matches the assignment.

status: accepted

```json
{
  "summary": "Good news: your own tests caught a real problem. One cookie test fails, so the suite exits with an error.",
  "items": [
    {
      "test_key": "student_tests_pass",
      "what_went_wrong": "test_cookie_default fails, so the student test suite does not pass.",
      "hint": "Before changing the test, compare what it expects Cookie() to start with and the default in Cookie's __init__. Which one matches the assignment?"
    }
  ],
  "next_step": "Run pytest yourself and read which cookie assertion fails."
}
```
