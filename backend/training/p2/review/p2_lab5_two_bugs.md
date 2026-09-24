<!-- p2-review | case=p2_lab5_two_bugs | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_two_bugs

**Lab 5: Operator Overloading** · `single_failure` · two independent bugs: no $ in __str__, and __mul__ multiplies only the cents

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
@@ -32,5 +32,5 @@
             return NotImplemented
         total_cents = (self.dollars * 100 + self.cents) * other
-        return Money(0, total_cents)
+        return Money(self.dollars, self.cents * other)
 
     def __rmul__(self, other: int) -> "Money":
```

## What the grader reported

- `str` (Money __str__() formats currency output as '$[dollars].[cents:02d]'): `E     + 3.50`
- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 4 = <money.Money object at 0x000001F291002E90>.dollars`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __add__() overloads '+' operator to add dollars and cents, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, addition, and equality, but there are issues with the string formatting and multiplication logic.

**Money __str__() formats currency output as '$[dollars].[cents:02d]'**: The string representation is missing the dollar sign symbol.
- 💡 How can you include a literal '$' character in your f-string?

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The multiplication result is not reflecting the correct total amount of dollars.
- 💡 When you create the new Money object in __mul__, what values are you passing to the constructor to ensure the total amount is preserved?

**Next step:** Review the __str__ method and the return statement in __mul__.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `str`, `mul`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Both hints gave the fix. Two separate problems, each pointing to where to look, and a next step to take them one at a time.

status: accepted

```json
{
  "summary": "Normalizing, addition and equality work. There are two separate things to fix: the string format and multiplication.",
  "items": [
    {
      "test_key": "str",
      "what_went_wrong": "str(m1) gave '3.50'; the test expects '$3.50'.",
      "hint": "Can you compare your output with the expected text character by character, starting from the left?"
    },
    {
      "test_key": "mul",
      "what_went_wrong": "Multiplying $3.50 by 2 gave 4 dollars instead of 7.",
      "hint": "Work out $3.50 times 2 by hand. Which part of the amount does your __mul__ multiply, and which part is left as it was?"
    }
  ],
  "next_step": "Fix one at a time: start with __str__, rerun the tests, then look at __mul__."
}
```
