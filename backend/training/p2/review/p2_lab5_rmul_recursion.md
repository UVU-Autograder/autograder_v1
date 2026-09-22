<!-- p2-review | case=p2_lab5_rmul_recursion | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_rmul_recursion

**Lab 5: Operator Overloading** · `single_failure` · __rmul__ returns other * self, which calls __rmul__ again forever (RecursionError)

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -36,5 +36,5 @@
     def __rmul__(self, other: int) -> "Money":
         """Right-multiply integer scalar by Money object."""
-        return self.__mul__(other)
+        return other * self
 
     def __eq__(self, other: object) -> bool:
```

## What the grader reported

- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `!!! Recursion detected (same locals & position)`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, string formatting, addition, and equality. However, there is a recursion issue with the multiplication operator.

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The code enters an infinite loop when trying to multiply an integer by a Money object, resulting in a RecursionError.
- 💡 When `__rmul__` calls `other * self`, how does Python interpret `other * self` in terms of which class's `__mul__` method is being called?

**Next step:** Review the logic in the `__rmul__` method in `money.py`.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `mul`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: the hint is a good tracing question.

status: todo

```json
{
  "summary": "Normalizing, formatting, addition and equality all work. Multiplying with the number on the left never finishes.",
  "items": [
    {
      "test_key": "mul",
      "what_went_wrong": "3 * m2 fails with a RecursionError: Python keeps calling the same method until it gives up.",
      "hint": "When __rmul__ runs other * self, which method does Python call to work that out? Can you trace one step further?"
    }
  ],
  "next_step": "Review the __rmul__ method in money.py."
}
```
