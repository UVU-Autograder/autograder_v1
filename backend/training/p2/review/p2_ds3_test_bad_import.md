<!-- p2-review | case=p2_ds3_test_bad_import | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds3_test_bad_import

**Dessert Shop 3: Test Cases with pytest** · `cascading_failure` · test file imports from desserts (typo), so pytest cannot collect it

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/test_dessert.py
+++ student/test_dessert.py
@@ -1,3 +1,3 @@
-from dessert import Candy, Cookie, DessertItem, IceCream, Sundae
+from desserts import Candy, Cookie, DessertItem, IceCream, Sundae
```

## What the grader reported

- `student_tests_pass` (Student test suite executes cleanly and passes all assertions): `E   Stderr:`
- Passing: DS2 class hierarchy and Order class methods intact, test_dessert.py exists and defines at least 15 valid test functions

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your test suite is failing to run because the test module cannot locate your source code.

**Student test suite executes cleanly and passes all assertions**: The test runner encountered a ModuleNotFoundError because it cannot find a module named 'desserts'.
- 💡 Check the filename of the file containing your classes and compare it to the import statement in test_dessert.py.

**Next step:** Verify the filename of your main class file and ensure it matches the name used in your test imports.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `student_tests_pass`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

status: accepted

```json
{
  "summary": "Your test suite is failing to run because the test module cannot locate your source code.",
  "items": [
    {
      "test_key": "student_tests_pass",
      "what_went_wrong": "The test runner encountered a ModuleNotFoundError because it cannot find a module named 'desserts'.",
      "hint": "Check the filename of the file containing your classes and compare it to the import statement in test_dessert.py."
    }
  ],
  "next_step": "Verify the filename of your main class file and ensure it matches the name used in your test imports."
}
```
