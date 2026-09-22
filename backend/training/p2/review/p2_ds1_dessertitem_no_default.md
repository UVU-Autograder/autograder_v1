<!-- p2-review | case=p2_ds1_dessertitem_no_default | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds1_dessertitem_no_default

**Dessert Shop 1: Inheritance Superclass** · `single_failure` · DessertItem name has no default, so DessertItem() fails

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -1,4 +1,4 @@
 class DessertItem:
-    def __init__(self, name: str = ""):
+    def __init__(self, name: str):
         self.name = name
```

## What the grader reported

- `dessert_item` (DessertItem base class defines name attribute with default ''): `E   TypeError: DessertItem.__init__() missing 1 required positional argument: 'name'`
- Passing: Candy inherits DessertItem and defines candy_weight & price_per_pound, Cookie inherits DessertItem and defines cookie_quantity & price_per_dozen, IceCream inherits DessertItem and defines scoop_count & price_per_scoop, Sundae inherits IceCream and defines topping_name & topping_price

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your inheritance structure is set up correctly, but there is an issue with how the base class handles its attributes.

**DessertItem base class defines name attribute with default ''**: The test failed because the DessertItem class requires a name to be provided during initialization, but the test tried to create an instance without one.
- 💡 How can you modify the DessertItem __init__ method to provide a default value for the name?

**Next step:** Review the DessertItem class definition.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `dessert_item`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Pre-edit note (Claude): The hint gave the fix ('provide a default value'). Now points to the subclasses, which already get this right.

status: todo

```json
{
  "summary": "Your inheritance structure is set up correctly, but there is an issue with how the base class handles its attributes.",
  "items": [
    {
      "test_key": "dessert_item",
      "what_went_wrong": "The test creates DessertItem() with no arguments, and your constructor requires a name.",
      "hint": "Can you compare the __init__ signature of DessertItem with Candy's? What lets Candy() work with no arguments?"
    }
  ],
  "next_step": "Review the DessertItem class definition."
}
```
