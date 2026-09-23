<!-- p2-review | case=p2_lab5_str_no_dollar_sign | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_str_no_dollar_sign

**Lab 5: Operator Overloading** · `single_failure` · __str__ leaves out the $

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -19,5 +19,5 @@
     def __str__(self) -> str:
         """Return formatted string $dollars.cents."""
-        return f"${self.dollars}.{self.cents:02d}"
+        return f"{self.dollars}.{self.cents:02d}"
 
     def __add__(self, other: Money) -> "Money":
```

## What the grader reported

- `str` (Money __str__() formats currency output as '$[dollars].[cents:02d]'): `E     + 3.50`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, addition, and multiplication, but there is a formatting issue with the string representation.

**Money __str__() formats currency output as '$[dollars].[cents:02d]'**: The string representation of the Money object is missing the currency symbol.
- 💡 How can you modify the f-string in your __str__ method to include the '$' symbol before the dollar amount?

**Next step:** Review the __str__ method in your Money class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `str`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint said how to add the '$' (the fix). Now asks for a character-by-character comparison.

status: accepted

```json
{
  "summary": "Normalizing, addition and multiplication all work. The string for a Money object is almost right.",
  "items": [
    {
      "test_key": "str",
      "what_went_wrong": "str(m1) gave '3.50'; the test expects '$3.50'.",
      "hint": "Can you compare your output with the expected text character by character, starting from the left?"
    }
  ],
  "next_step": "Review the __str__ method in your Money class."
}
```
