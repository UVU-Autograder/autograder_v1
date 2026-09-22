<!-- p2-review | case=p2_lab5_str_float_math | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_str_float_math

**Lab 5: Operator Overloading** · `single_failure` · __str__ builds the amount with float division ($3.5)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -19,5 +19,5 @@
     def __str__(self) -> str:
         """Return formatted string $dollars.cents."""
-        return f"${self.dollars}.{self.cents:02d}"
+        return f"${self.dollars + self.cents / 100}"
 
     def __add__(self, other: Money) -> "Money":
```

## What the grader reported

- `str` (Money __str__() formats currency output as '$[dollars].[cents:02d]'): `E     + $3.5`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, addition, and multiplication, but there is an issue with the string representation format.

**Money __str__() formats currency output as '$[dollars].[cents:02d]'**: The string output for the Money object is missing a leading zero for cents when the value is less than 100.
- 💡 How can you use f-string formatting to ensure the cents portion always displays as two digits?

**Next step:** Review the f-string documentation for padding and precision formatting.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `str`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft misread it as a zero-padding problem. The real cause is building the text from float arithmetic.

status: todo

```json
{
  "summary": "Normalizing, addition and multiplication all work. The string for a Money object loses a digit.",
  "items": [
    {
      "test_key": "str",
      "what_went_wrong": "str(m1) gave '$3.5'; the test expects '$3.50'.",
      "hint": "Your __str__ builds the amount with arithmetic. What happens to the trailing zero when Python turns the number 3.5 into text?"
    }
  ],
  "next_step": "Compare your __str__ with the format the assignment gives: dollars, a dot, then cents as two digits."
}
```
