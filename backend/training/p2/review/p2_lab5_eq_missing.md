<!-- p2-review | case=p2_lab5_eq_missing | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_eq_missing

**Lab 5: Operator Overloading** · `single_failure` · no __eq__ at all, so == falls back to identity

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -38,9 +38,4 @@
         return self.__mul__(other)
 
-    def __eq__(self, other: object) -> bool:
-        """Check equality after normalization."""
-        if not isinstance(other, Money):
-            return False
-        return (self.dollars, self.cents) == (other.dollars, other.cents)
```

## What the grader reported

- `eq` (Money __eq__() overloads '==' operator comparing normalized total cents): `E   assert <money.Money object at 0x106eb81a0> == <money.Money object at 0x106dfa0d0>`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __add__() overloads '+' operator to add dollars and cents, Money __mul__() and __rmul__() overload '*' operator for scalar multiplication

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented the normalization, string formatting, addition, and multiplication logic for the Money class.

**Money __eq__() overloads '==' operator comparing normalized total cents**: The equality comparison between two Money objects is returning False when it should be True.
- 💡 How does your __eq__ method determine if two Money objects are equal?

**Next step:** Review the requirements for the __eq__ method and ensure it compares the normalized total cents.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `eq`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The draft asked how 'your __eq__' works, but there is no __eq__. Now asks which listed operators the class defines.

status: todo

```json
{
  "summary": "You have implemented normalization, string formatting, addition and multiplication. Two equal amounts do not compare as equal.",
  "items": [
    {
      "test_key": "eq",
      "what_went_wrong": "m1 == m2 was False for two Money objects holding the same amount.",
      "hint": "Without a method of your own, how does Python decide whether two objects are ==? Which of the operators the assignment lists can you find a method for in your class?"
    }
  ],
  "next_step": "Compare the operators the assignment lists with the methods in your Money class."
}
```
