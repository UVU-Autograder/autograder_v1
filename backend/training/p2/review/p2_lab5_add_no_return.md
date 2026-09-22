<!-- p2-review | case=p2_lab5_add_no_return | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_add_no_return

**Lab 5: Operator Overloading** · `single_failure` · __add__ builds the result but forgets to return it

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -25,5 +25,5 @@
         if not isinstance(other, Money):
             return NotImplemented
-        return Money(self.dollars + other.dollars, self.cents + other.cents)
+        Money(self.dollars + other.dollars, self.cents + other.cents)
 
     def __mul__(self, other: int) -> "Money":
```

## What the grader reported

- `add` (Money __add__() overloads '+' operator to add dollars and cents): `E    +  where False = isinstance(None, <class 'money.Money'>)`
- Passing: Money normalize() carries overflow cents (>= 100) into dollars, Money __str__() formats currency output as '$[dollars].[cents:02d]', Money __mul__() and __rmul__() overload '*' operator for scalar multiplication, Money __eq__() overloads '==' operator comparing normalized total cents

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

You have successfully implemented most of the operator overloading requirements, including normalization, string formatting, and multiplication.

**Money __add__() overloads '+' operator to add dollars and cents**: The addition operation is returning None instead of a new Money object.
- 💡 Does your __add__ method actually return the result of the new Money object you are creating?

**Next step:** Review the return statement in the __add__ method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `add`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('does it return the result'). Now compares with __mul__, which returns its Money.

status: todo

```json
{
  "summary": "Normalizing, formatting and multiplication all work. Addition gives back nothing.",
  "items": [
    {
      "test_key": "add",
      "what_went_wrong": "m1 + m2 gave back None instead of a Money object.",
      "hint": "Compare the last line of __add__ with the last line of __mul__. What does __mul__ do with the Money it builds?"
    }
  ],
  "next_step": "Review the __add__ method in money.py."
}
```
