<!-- p2-review | case=p2_ds2_add_overwrites | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_add_overwrites

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · Order.add replaces the list with [item]

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -38,5 +38,5 @@
 
     def add(self, item: DessertItem) -> None:
-        self.order.append(item)
+        self.order = [item]
 
     def __len__(self) -> int:
```

## What the grader reported

- `order_class` (Order class defines order list, add() method, and len() support): `E    +  where 1 = len(<dessert.Order object at 0x00000147570B2BA0>)`
- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E    +  where 2 = len(['Oatmeal Raisin', 'Total number of items in order: 1'])`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but there are issues with how items are being stored and displayed in the order.

**Order class defines order list, add() method, and len() support**: The length of the order is only reflecting the most recently added item instead of the full collection.
- 💡 In your add method, what happens to the existing items in the list when a new one is assigned?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The final output contains fewer lines than expected, suggesting some items are not being printed.
- 💡 If the order length is incorrect, how might that affect the loop that prints the item names?

**Next step:** Review the logic inside the Order.add method.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> v8 revision (Claude): tightened wording; follow-on item now points back to Order.add; trimmed

> p3b (Claude): trimmed under 65 words

status: accepted

```json
{
  "summary": "Your class hierarchy works, but the order keeps only the latest item.",
  "items": [
    {
      "test_key": "order_class",
      "what_went_wrong": "After several adds, the order's length counts only the last item.",
      "hint": "In Order.add, what happens to the items already in the order?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "The receipt prints fewer lines than expected for the same reason.",
      "hint": "This follows from the Order.add problem; fix that first."
    }
  ],
  "next_step": "Review the Order.add method in dessert.py."
}
```
