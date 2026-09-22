<!-- p2-review | case=p2_lab5_normalize_single_carry | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_normalize_single_carry

**Lab 5: Operator Overloading** · `single_failure` · normalize carries only one dollar, so 250 cents becomes $1.150

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -14,6 +14,6 @@
         """Carry cents >= 100 over to dollars."""
         if self.cents >= 100:
-            self.dollars += self.cents // 100
-            self.cents = self.cents % 100
+            self.dollars += 1
+            self.cents = self.cents - 100
 
     def __str__(self) -> str:
```

## What the grader reported

- `normalize` (Money normalize() carries overflow cents (>= 100) into dollars): `E    +  where 1 = <money.Money object at 0x10aa68f50>.dollars`
- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 1 = <money.Money object at 0x10aa6a5d0>.dollars`
- Passing: Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the string formatting, addition, and equality logic for the Money class. However, there are issues with how values are normalized and multiplied.

**Money normalize() carries overflow cents (>= 100) into dollars**: The normalize method only carries over 100 cents once, which fails when the cents value is 200 or greater.
- 💡 How can you modify the logic in normalize to handle cases where cents are much larger than 100?

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The multiplication result is not being correctly normalized into the expected dollar and cent format.
- 💡 When you create a new Money object from total_cents, what happens if total_cents is greater than 100?

**Next step:** Review the logic in the normalize method to ensure it handles any amount of overflow.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `normalize`, `mul`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint and what_went_wrong gave the fix. Now asks the student to trace a large amount by hand.

status: todo

```json
{
  "summary": "Formatting, addition and equality work. normalize handles small overflows but not large ones, and multiplication inherits that.",
  "items": [
    {
      "test_key": "normalize",
      "what_went_wrong": "After normalizing, the test expected 3 dollars and got 1.",
      "hint": "Can you trace normalize by hand with 350 cents? How many dollars should come out, and how many does your code carry?"
    },
    {
      "test_key": "mul",
      "what_went_wrong": "The product has 1 dollar instead of 7, because its cents are not fully carried.",
      "hint": "This follows from the normalize problem. Fix that first."
    }
  ],
  "next_step": "Review the normalize method in money.py."
}
```
