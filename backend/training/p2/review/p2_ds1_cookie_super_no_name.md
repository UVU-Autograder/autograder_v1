<!-- p2-review | case=p2_ds1_cookie_super_no_name | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_cookie_super_no_name

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · Cookie calls super().__init__() without passing name

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -13,5 +13,5 @@
 class Cookie(DessertItem):
     def __init__(self, name: str = "", cookie_quantity: int = 0, price_per_dozen: float = 0.0):
-        super().__init__(name)
+        super().__init__()
         self.cookie_quantity = cookie_quantity
         self.price_per_dozen = price_per_dozen
```

## What the grader reported

- `cookie` (Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen): `E     - Chocolate Chip`
- Passing: DessertItem base class defines name attribute with default '', Candy inherits DessertItem and defines candy_weight & price_per_pound, IceCream inherits DessertItem and defines scoop_count & price_per_scoop, Sundae inherits IceCream and defines topping_name & topping_price

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your dessert classes are well-structured, but there is an issue with how the Cookie class handles its name.

**Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen**: The name of the Cookie instance is being set to an empty string instead of the provided name.
- 💡 How is the 'name' argument being passed to the superclass constructor in the Cookie class?

**Next step:** Review the Cookie class __init__ method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `cookie`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

status: accepted

```json
{
  "summary": "Your dessert classes are well-structured, but there is an issue with how the Cookie class handles its name.",
  "items": [
    {
      "test_key": "cookie",
      "what_went_wrong": "The name of the Cookie instance is being set to an empty string instead of the provided name.",
      "hint": "How is the 'name' argument currently being passed to the superclass constructor in the Cookie class?"
    }
  ],
  "next_step": "Review the Cookie class __init__ method."
}
```
