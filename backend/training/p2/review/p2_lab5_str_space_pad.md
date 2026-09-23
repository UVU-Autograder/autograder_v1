<!-- p2-review | case=p2_lab5_str_space_pad | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_str_space_pad

**Lab 5: Operator Overloading** · `single_failure` · cents formatted with :2d, which pads with a space ($3. 5)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -19,5 +19,5 @@
     def __str__(self) -> str:
         """Return formatted string $dollars.cents."""
-        return f"${self.dollars}.{self.cents:02d}"
+        return f"${self.dollars}.{self.cents:2d}"
 
     def __add__(self, other: Money) -> "Money":
```

## What the grader reported

- `str` (Money __str__() formats currency output as '$[dollars].[cents:02d]'): `E     ?    ^`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, addition, and multiplication. However, there is a formatting issue with the string representation.

**Money __str__() formats currency output as '$[dollars].[cents:02d]'**: The string representation includes an extra space between the decimal point and the cents.
- 💡 How does the format specifier :2d behave compared to :02d?

**Next step:** Review the f-string formatting syntax in the __str__ method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `str`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint compared :2d with :02d (an either/or with the answer). Now asks the student to see what the spec does to a one-digit number.

status: accepted

```json
{
  "summary": "Normalizing, addition and multiplication all work. Amounts with fewer than 10 cents print with a gap.",
  "items": [
    {
      "test_key": "str",
      "what_went_wrong": "str(m2) gave '$5. 5'; the test expects '$5.05'.",
      "hint": "Look at the format spec you use for the cents. What does it put in front of a one-digit number like 5? Try printing just the cents part to see."
    }
  ],
  "next_step": "Review the cents part of the f-string in __str__."
}
```
