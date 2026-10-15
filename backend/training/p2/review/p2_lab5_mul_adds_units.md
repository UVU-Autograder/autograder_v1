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

- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 1 = <money.Money object at 0x000002707F672C10>.dollars`
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

> v8 revision (Claude): removed the amounts; next_step no longer names the exact line

status: accepted

```json
{
  "summary": "Normalizing, formatting, addition, and equality all work, but multiplication gives too small an amount.",
  "items": [
    {
      "test_key": "mul",
      "what_went_wrong": "Multiplying a Money by a whole number gives far fewer dollars than the test expects.",
      "hint": "Trace __mul__ by hand with the test's amount: how many cents does your code think that amount is worth?"
    }
  ],
  "next_step": "Review the __mul__ method in money.py."
}
```
