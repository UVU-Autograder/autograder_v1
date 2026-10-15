<!-- p2-review | case=p2_lab5_normalize_not_called | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_lab5_normalize_not_called

**Lab 5: Operator Overloading** · `single_failure` · __init__ never calls normalize()

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/money.py
+++ student/money.py
@@ -9,5 +9,4 @@
         self.dollars = int(dollars)
         self.cents = int(cents)
-        self.normalize()
 
     def normalize(self) -> None:
```

## What the grader reported

- `normalize` (Money normalize() carries overflow cents (>= 100) into dollars): `E    +  where 1 = <money.Money object at 0x0000014E1C872BA0>.dollars`
- `add` (Money __add__() overloads '+' operator to add dollars and cents): `E    +  where 5 = <money.Money object at 0x0000014E1C85EE90>.dollars`
- `mul` (Money __mul__() and __rmul__() overload '*' operator for scalar multiplication): `E    +  where 0 = <money.Money object at 0x0000014E1C85F750>.dollars`
- `eq` (Money __eq__() overloads '==' operator comparing normalized total cents): `E   assert <money.Money object at 0x0000014E1C873620> == <money.Money object at 0x0000014E1C85F9D0>`
- Passing: Money __str__() formats currency output as '$[dollars].[cents:02d]'

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your implementation of the currency formatting is correct, but there are issues with how values are normalized and compared.

**Money normalize() carries overflow cents (>= 100) into dollars**: The normalize method is not being called automatically during initialization or after operations, leaving the dollar and cent values in an unnormalized state.
- 💡 How can you ensure that the normalization logic is applied whenever a new Money object is created or modified?

**Money __add__() overloads '+' operator to add dollars and cents**: The sum of two Money objects results in a value where the cents are not carried over to the dollars.
- 💡 What happens to the total cents when you add two Money objects together?

**Money __mul__() and __rmul__() overload '*' operator for scalar multiplication**: The multiplication result is not being normalized, leading to incorrect dollar and cent values.
- 💡 Does the new Money object created in __mul__ have its cents carried over to dollars?

**Money __eq__() overloads '==' operator comparing normalized total cents**: The equality check fails because the objects are being compared before they are normalized.
- 💡 Should you normalize the objects before comparing their dollar and cent attributes?

**Next step:** Review the `__init__` method and consider where `normalize()` should be called.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `normalize`, `add`, `mul`, `eq`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): 4 items cut to 3; the hint and next step gave the fix, and the eq item misdiagnosed. One root cause: normalize never runs.

> v8 revision (Claude): removed the dollar values and the test's constructor call; hint no longer asks where normalize is called; trimmed

> p3b (Claude): shortened summary, first item and add hint to fit 65 words

> p4 (Claude): trimmed to 55 words or fewer; follow-on items kept brief (p3b ran 87-106 words on 3-item cascades)

status: accepted

```json
{
  "summary": "Your formatting works, but extra cents never carry into dollars.",
  "items": [
    {
      "test_key": "normalize",
      "what_went_wrong": "A new Money keeps its overflow cents.",
      "hint": "Trace what runs when a Money is created: does your carrying logic ever run?"
    },
    {
      "test_key": "add",
      "what_went_wrong": "The sum has too few dollars.",
      "hint": "Same cause."
    },
    {
      "test_key": "mul",
      "what_went_wrong": "The product is short too.",
      "hint": "Same fix."
    }
  ],
  "next_step": "Trace Money.__init__; the eq test clears too."
}
```
