<!-- p2-review | case=p2_lab5_init_renamed_params | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_init_renamed_params

**Lab 5: Operator Overloading** · `cascading_failure` · __init__ parameters renamed to d and c but the body still uses dollars and cents (NameError)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -5,5 +5,5 @@
     """Represents currency using integer dollars and cents with overloaded operators."""
 
-    def __init__(self, dollars: int, cents: int) -> None:
+    def __init__(self, d: int, c: int) -> None:
         """Initialize dollars and cents and normalize."""
         self.dollars = int(dollars)
```

## What the grader reported

- `normalize` (Money normalize() carries overflow cents (>= 100) into dollars): `E   NameError: name 'dollars' is not defined`
- `str` (Money __str__() formats currency output as '$[dollars].[cents:02d]'): `E   NameError: name 'dollars' is not defined`
- `add` (Money __add__() overloads '+' operator to add dollars and cents): `E   NameError: name 'dollars' is not defined`
- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E   NameError: name 'dollars' is not defined`
- `eq` (Money __eq__() overloads '==' operator comparing normalized total cents): `E   NameError: name 'dollars' is not defined`

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

The submission is currently unable to run any tests because of a scope error in the constructor.

**Money normalize() carries overflow cents (>= 100) into dollars**: The code attempts to access a variable named 'dollars' that hasn't been defined in the scope of the __init__ method.
- 💡 How do you access the arguments passed into the __init__ method's parameters?

**Money __str__() formats currency output as '$[dollars].[cents:02d]'**: This failure follows from the NameError in the constructor.
- 💡 Check the constructor's parameter names.

**Money __add__() overloads '+' operator to add dollars and cents**: This failure follows from the NameError in the constructor.
- 💡 Check the constructor's parameter names.

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: This failure follows from the NameError in the constructor.
- 💡 Check the constructor's parameter names.

**Money __eq__() overloads '==' operator comparing normalized total cents**: This failure follows from the NameError in the constructor.
- 💡 Check the constructor's parameter names.

**Next step:** Review the __init__ method signature and how it handles its parameters.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `normalize`, `str`, `add`, `mul`, `eq`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 5 items cut to 3; one root cause (the parameter names), the rest follow.

status: accepted

```json
{
  "summary": "Your operator methods are written, but creating any Money fails, so every test stops there.",
  "items": [
    {
      "test_key": "normalize",
      "what_went_wrong": "Creating a Money fails with \"NameError: name 'dollars' is not defined\".",
      "hint": "Compare the parameter names on the def __init__ line with the names used in the lines below it."
    },
    {
      "test_key": "str",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This follows from __init__. Fix that first."
    },
    {
      "test_key": "add",
      "what_went_wrong": "This test fails for the same reason.",
      "hint": "This clears once a Money can be created."
    }
  ],
  "next_step": "Review __init__ in money.py. The mul and eq tests fail for the same reason."
}
```
