<!-- p2-review | case=p2_lab5_mul_adds_units | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_mul_adds_units

**Lab 5: Operator Overloading** · `single_failure` · __mul__ adds dollars and cents instead of converting to total cents

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -31,5 +31,5 @@
         if not isinstance(other, int):
             return NotImplemented
-        total_cents = (self.dollars * 100 + self.cents) * other
+        total_cents = (self.dollars + self.cents) * other
         return Money(0, total_cents)
```

## What the grader reported

- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 1 = <money.Money object at 0x1069fe0d0>.dollars`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, string formatting, addition, and equality. However, there is an issue with the multiplication logic.

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The multiplication result is not producing the expected dollar amount.
- 💡 How are you calculating the total amount of cents before creating the new Money object?

**Next step:** Review the logic inside the __mul__ method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `mul`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Small edit: the hint now asks the student to work the example by hand.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Normalizing, formatting, addition and equality all work. Multiplication gives the wrong amount.",
  "items": [
    {
      "test_key": "mul",
      "what_went_wrong": "Multiplying $3.50 by 2 gave 1 dollar; the test expects 7.",
      "hint": "How are you working out the total number of cents before creating the new Money? Can you do it by hand for $3.50?"
    }
  ],
  "next_step": "Review the total_cents line in __mul__."
}
```
