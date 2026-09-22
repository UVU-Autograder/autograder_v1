<!-- p2-review | case=p2_lab5_all_pass_divmod | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_all_pass_divmod

**Lab 5: Operator Overloading** · `all_pass` · valid alternative: normalize with divmod

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -13,7 +13,6 @@
     def normalize(self) -> None:
         """Carry cents >= 100 over to dollars."""
-        if self.cents >= 100:
-            self.dollars += self.cents // 100
-            self.cents = self.cents % 100
+        extra, self.cents = divmod(self.cents, 100)
+        self.dollars += extra
 
     def __str__(self) -> str:
```

## What the grader reported

- All automated checks passed.
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Great job! Your implementation of operator overloading for the Money class is fully functional and passed all test cases.

**Next step:** Consider how you might extend this class to support subtraction or division using the same operator overloading principles.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given. Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): Generic extension replaced with one about the student's own choice (divmod).

status: todo

```json
{
  "summary": "Great job! Every operator test passes.",
  "items": [],
  "next_step": "Your normalize uses divmod, which works without an if. Can you work out what it does with negative cents, and whether Money should allow them?"
}
```
