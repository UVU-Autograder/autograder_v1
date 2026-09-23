<!-- p2-review | case=p2_lab5_class_lowercase | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_class_lowercase

**Lab 5: Operator Overloading** · `cascading_failure` · class named money instead of Money; every test fails on the same missing name

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -2,5 +2,5 @@
 
 
-class Money:
+class money:
     """Represents currency using integer dollars and cents with overloaded operators."""
 
@@ -47,5 +47,5 @@
 def main() -> None:
     """Main testing entrypoint."""
-    m1 = Money(3, 50)
+    m1 = money(3, 50)
     m2 = Money(2, 75)
     print("m1:", m1)
```

## What the grader reported

- `normalize` (Money normalize() carries overflow cents (>= 100) into dollars): `E   AttributeError: module 'money' has no attribute 'Money'. Did you mean: 'money'?`
- `str` (Money __str__() formats currency output as '$[dollars].[cents:02d]'): `E   AttributeError: module 'money' has no attribute 'Money'. Did you mean: 'money'?`
- `add` (Money __add__() overloads '+' operator to add dollars and cents): `E   AttributeError: module 'money' has no attribute 'Money'. Did you mean: 'money'?`
- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E   AttributeError: module 'money' has no attribute 'Money'. Did you mean: 'money'?`
- `eq` (Money __eq__() overloads '==' operator comparing normalized total cents): `E   AttributeError: module 'money' has no attribute 'Money'. Did you mean: 'money'?`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

The autograder is unable to locate the Money class within your module, causing all tests to fail.

**Money normalize() carries overflow cents (>= 100) into dollars**: The test suite cannot find a class named 'Money' in your file.
- 💡 How does the capitalization of your class name affect how it is accessed by other modules?

**Money __str__() formats currency output as '$[dollars].[cents:02d]'**: The test suite cannot find a class named 'Money' in your file.
- 💡 Check the capitalization of your class definition.

**Money __add__() overloads '+' operator to add dollars and cents**: The test suite cannot find a class named 'Money' in your file.
- 💡 Check the capitalization of your class definition.

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The test suite cannot find a class named 'Money' in your file.
- 💡 Check the capitalization of your class definition.

**Money __eq__() overloads '==' operator comparing normalized total cents**: The test suite cannot find a class named 'Money' in your file.
- 💡 Check the capitalization of your class definition.

**Next step:** Review the class definition line in money.py to ensure it matches the expected naming convention.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `normalize`, `str`, `add`, `mul`, `eq`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 5 identical items cut to 3: one root cause (the class name), the rest follow from it.

status: accepted

```json
{
  "summary": "Your Money logic is written, but nothing can find the class by the name the assignment uses, so every test fails.",
  "items": [
    {
      "test_key": "normalize",
      "what_went_wrong": "The test cannot find a class named Money in money.py.",
      "hint": "The error ends with \"Did you mean: 'money'?\". How does the capitalization of your class name compare with the name the assignment uses?"
    },
    {
      "test_key": "str",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This follows from the class name. Fix that first."
    },
    {
      "test_key": "add",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This clears once the class name matches."
    }
  ],
  "next_step": "Review the class line in money.py. The mul and eq tests fail for the same reason."
}
```
