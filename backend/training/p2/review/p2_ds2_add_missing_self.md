<!-- p2-review | case=p2_ds2_add_missing_self | drafted_by=gemma4-12b-qat | prompt=v4 -->
# p2_ds2_add_missing_self

**Dessert Shop 2: Using Classes in main** · `cascading_failure` · Order.add defined without self

## The bug (ground truth -- the model never sees this diff)

```diff
--- model/dessert.py
+++ student/dessert.py
@@ -37,5 +37,5 @@
         self._index: int = 0
 
-    def add(self, item: DessertItem) -> None:
+    def add(item: DessertItem) -> None:
         self.order.append(item)
```

## What the grader reported

- `order_class` (Order class defines order list, add() method, and len() support): `E   TypeError: Order.add() takes 1 positional argument but 2 were given`
- `main_output` (dessertshop.py main() constructs Order items and prints formatted receipt): `E   AssertionError: dessertshop.py execution failed: Order.add() takes 1 positional argument but 2 were given`
- Passing: DS1 class hierarchy intact (DessertItem, Candy, Cookie, IceCream, Sundae)

## Draft by `gemma4-12b-qat` (prompt v4), as the student would see it

Your class hierarchy is correctly implemented, but there is an issue with how the Order class methods are defined.

**Order class defines order list, add() method, and len() support**: The add method is receiving more arguments than it is prepared to handle.
- 💡 How should a method inside a class be defined to receive the instance of the object as its first argument?

**dessertshop.py main() constructs Order items and prints formatted receipt**: The main function failed to execute because of a TypeError in the Order.add method.
- 💡 If the add method is fixed, will the main function be able to complete its execution?

**Next step:** Review the definition of the add method in the Order class.

Automatic checks on the draft: pass

## Your version

Edit the JSON, keeping each `test_key` as given (allowed: `order_class`, `main_output`). Then set the status to `approved` to train on it, or `rejected` to leave it out.

- The hint and next step point to **where to look**, never what to write. Naming the function that has the bug is fine; naming a missing method, the operator or value to use, or an either/or with the answer in it is not.
- Every sentence matches the assertion and the diff above. Nothing about bugs the grader did not report.
- One root cause is explained once; the other items say they follow from it.
- Encouraging, plain language, starts with what works, under 150 words.
- all-pass cases keep `"items": []`.

> Stale after 4159d52 (tightened tests): the assertion messages changed. Re-check the target against the new grader output before approving.

status: todo

```json
{
  "summary": "Your class hierarchy is correctly implemented, but there is an issue with how the Order class methods are defined.",
  "items": [
    {
      "test_key": "order_class",
      "what_went_wrong": "The add method is receiving more arguments than it is prepared to handle.",
      "hint": "How should a method inside a class be defined to receive the instance of the object as its first argument?"
    },
    {
      "test_key": "main_output",
      "what_went_wrong": "The main function failed to execute because of a TypeError in the Order.add method.",
      "hint": "If the add method is fixed, will the main function be able to complete its execution?"
    }
  ],
  "next_step": "Review the definition of the add method in the Order class."
}
```
