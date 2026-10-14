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

- `normalize` (Money normalize() carries overflow cents (>= 100) into dollars): `E    +  where 1 = <money.Money object at 0x000001A6DF5D1F90>.dollars`
- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 1 = <money.Money object at 0x000001A6DF5D34D0>.dollars`
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

> v8 revision (Claude): removed the dollar amounts and the example cent value; trimmed

> p3b (Claude): shortened both items to fit 65 words

status: accepted

```json
{
  "summary": "Formatting, addition, and equality work, but normalize only handles small overflows.",
  "items": [
    {
      "test_key": "normalize",
      "what_went_wrong": "With a large cent amount, normalize carries fewer dollars than the test expects.",
      "hint": "Trace normalize by hand with several dollars' worth of cents: how many dollars get carried?"
    },
    {
      "test_key": "mul",
      "what_went_wrong": "The product has too few dollars for the same reason.",
      "hint": "This follows from the normalize problem; fix that first."
    }
  ],
  "next_step": "Review the normalize method in money.py."
}
```
