<!-- p2-review | case=p2_lab5_mul_forgets_dollars | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_mul_forgets_dollars

**Lab 5: Operator Overloading** · `single_failure` · __mul__ multiplies only the cents

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -32,5 +32,5 @@
             return NotImplemented
         total_cents = (self.dollars * 100 + self.cents) * other
-        return Money(0, total_cents)
+        return Money(self.dollars, self.cents * other)
 
     def __rmul__(self, other: int) -> "Money":
```

## What the grader reported

- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 4 = <money.Money object at 0x00000222B25E2C10>.dollars`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, string formatting, addition, and equality. However, there is an issue with how multiplication is calculated.

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The multiplication result shows a dollar value of 4 instead of the expected 7.
- 💡 When you calculate the new Money object, are you passing the correct total dollar and cent values to the constructor?

**Next step:** Review the `__mul__` method to see how the new `Money` instance is being initialized.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `mul`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint was vague ('correct values'). Now asks which part of the amount gets multiplied.

> v8 revision (Claude): removed the amounts and dollar counts; describes too few dollars in words

status: accepted

```json
{
  "summary": "Normalizing, formatting, addition and equality all work, but multiplication comes out too small.",
  "items": [
    {
      "test_key": "mul",
      "what_went_wrong": "Multiplying a Money amount gives too few dollars, so part of the amount is not being multiplied.",
      "hint": "Can you work out a multiplication by hand and compare it with your __mul__; which part of the amount does it multiply?"
    }
  ],
  "next_step": "Review what __mul__ returns in the Money class."
}
```
