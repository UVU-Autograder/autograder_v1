<!-- p2-review | case=p2_lab5_add_wrong_type_check | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_add_wrong_type_check

**Lab 5: Operator Overloading** · `single_failure` · __add__ checks isinstance(other, int), so adding two Money objects returns NotImplemented

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -23,5 +23,5 @@
     def __add__(self, other: Money) -> "Money":
         """Add two Money objects."""
-        if not isinstance(other, Money):
+        if not isinstance(other, int):
             return NotImplemented
         return Money(self.dollars + other.dollars, self.cents + other.cents)
```

## What the grader reported

- `add` (Money __add__() overloads '+' operator to add dollars and cents): `E   TypeError: unsupported operand type(s) for +: 'Money' and 'Money'`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation successfully handles normalization, string formatting, multiplication, and equality. However, there is an issue with how the addition operator is defined.

**Money __add__() overloads '+' operator to add dollars and cents**: The program raised a TypeError when trying to add two Money objects.
- 💡 In your __add__ method, what type of object is your current check expecting the 'other' variable to be?

**Next step:** Review the __add__ method in your Money class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `add`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): No change to the substance: the hint points exactly at the type check.

status: accepted

```json
{
  "summary": "Normalizing, formatting, multiplication and equality all work. Adding two Money objects fails.",
  "items": [
    {
      "test_key": "add",
      "what_went_wrong": "m1 + m2 raised \"unsupported operand type(s) for +: 'Money' and 'Money'\".",
      "hint": "In your __add__ method, what type of object is your check expecting other to be?"
    }
  ],
  "next_step": "Review the type check at the top of __add__."
}
```
