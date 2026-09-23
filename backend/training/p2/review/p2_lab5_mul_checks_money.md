<!-- p2-review | case=p2_lab5_mul_checks_money | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_mul_checks_money

**Lab 5: Operator Overloading** · `single_failure` · __mul__ checks isinstance(other, Money) instead of int, so money * 2 returns NotImplemented

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -29,5 +29,5 @@
     def __mul__(self, other: int) -> "Money":
         """Multiply Money by an integer scalar."""
-        if not isinstance(other, int):
+        if not isinstance(other, Money):
             return NotImplemented
         total_cents = (self.dollars * 100 + self.cents) * other
```

## What the grader reported

- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E   TypeError: unsupported operand type(s) for *: 'Money' and 'int'`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, string formatting, addition, and equality. However, there is an issue with how the multiplication operator is being handled.

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The program raised a TypeError when trying to multiply a Money object by an integer.
- 💡 Inside your __mul__ method, what condition are you checking to decide whether to return NotImplemented?

**Next step:** Review the type hints and logic in the __mul__ method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `mul`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Kept the good hint; the next step no longer mentions type hints, which are not the problem.

status: accepted

```json
{
  "summary": "Normalizing, formatting, addition and equality all work. Multiplying by a number fails.",
  "items": [
    {
      "test_key": "mul",
      "what_went_wrong": "money * 2 raised \"unsupported operand type(s) for *: 'Money' and 'int'\".",
      "hint": "Inside your __mul__ method, what condition decides whether to return NotImplemented? What type is other in money * 2?"
    }
  ],
  "next_step": "Review the type check at the top of __mul__."
}
```
