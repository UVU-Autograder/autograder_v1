<!-- p2-review | case=p2_lab5_eq_dollars_only | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_eq_dollars_only

**Lab 5: Operator Overloading** · `single_failure` · __eq__ compares only dollars

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -42,5 +42,5 @@
         if not isinstance(other, Money):
             return False
-        return (self.dollars, self.cents) == (other.dollars, other.cents)
+        return self.dollars == other.dollars
```

## What the grader reported

- `eq` (Money __eq__() overloads '==' operator comparing normalized total cents): `E   assert <money.Money object at 0x1073cc1a0> != <money.Money object at 0x10732a850>`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, string formatting, addition, and multiplication. However, there is an issue with how equality is determined.

**Money __eq__() overloads '==' operator comparing normalized total cents**: The equality check is returning a result that does not match the expected comparison for two Money objects.
- 💡 Does comparing only the dollars attribute account for cases where the cents might differ?

**Next step:** Review the __eq__ method in your Money class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `eq`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('comparing only dollars'). Now asks the student to trace two amounts that differ only in cents.

status: todo

```json
{
  "summary": "Normalizing, formatting, addition and multiplication all work. Equality treats two different amounts as the same.",
  "items": [
    {
      "test_key": "eq",
      "what_went_wrong": "m1 != m3 was False: two amounts with the same dollars but different cents compared as equal.",
      "hint": "Can you trace __eq__ for $3.50 and $3.49? Which part of each amount does it look at?"
    }
  ],
  "next_step": "Review the __eq__ method in your Money class."
}
```
